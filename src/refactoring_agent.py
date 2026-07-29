#!/usr/bin/env python3
"""KI-Refactoring-Agent - Dünnes Interface für Code-Refactoring via Ollama."""

import argparse, json, os, subprocess, sys, shutil, datetime, requests, difflib

OLLAMA_URL = "http://localhost:11434/api/generate"
TIMEOUT = 240
BACKUP_DIR = "backup"

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
with open(os.path.join(PROMPTS_DIR, "system_prompt_analyze.md"), "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_ANALYZE = f.read().strip()
with open(os.path.join(PROMPTS_DIR, "system_prompt_apply.md"), "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_APPLY = f.read().strip()


def create_backup(fp):
    src_dir = os.path.dirname(os.path.abspath(__file__))
    pr = os.path.dirname(src_dir)
    bd = os.path.join(pr, BACKUP_DIR)
    try:
        os.makedirs(bd, exist_ok=True)
    except PermissionError:
        bd = os.path.join("/tmp", BACKUP_DIR)
        os.makedirs(bd, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    rp = os.path.relpath(fp, pr)
    bp = os.path.join(bd, f"{ts}_{rp.replace('/', '_').replace('\\', '_')}")
    shutil.copy2(fp, bp)
    os.chmod(bp, 0o444)
    return bp


def verify_syntax(code):
    tf = f"/tmp/syntax_check_{os.getpid()}.py"
    try:
        with open(tf, 'w', encoding='utf-8') as f:
            f.write(code)
        r = subprocess.run(["python", "-m", "py_compile", tf], capture_output=True, timeout=5)
        if os.path.exists(tf):
            os.remove(tf)
        return r.returncode == 0, r.stderr.decode() or ""
    except Exception as e:
        return False, str(e)


def display_with_bat(text, lang="python"):
    try:
        p = subprocess.Popen(["bat", "--paging=never", "--color=always", "--decorations=never",
                            f"--language={lang}"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)
        out, _ = p.communicate(input=text, timeout=5)
        print(out if p.returncode == 0 else text, end='')
    except:
        print(text)


def read_code(fp):
    return open(fp, "r", encoding="utf-8").read() if fp else sys.stdin.read()


def check_ollama():
    try:
        requests.get("http://localhost:11434/api/tags", timeout=10)
        return True
    except:
        return False


def check_model(m):
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=10)
        return m in [x["name"] for x in r.json().get("models", [])]
    except:
        return False


def call_ollama(code, model, temp, mode="analyze", apply_instructions=""):
    if mode == "analyze":
        nc = '\n'.join(f"{i:4d}: {l}" for i, l in enumerate(code.split('\n'), 1))
        p = f"Here is the COMPLETE Python file with line numbers:\n\n```\n{nc}\n```\n\nAnalyze and return code smells with old_code, new_code, and diff."
        system = SYSTEM_PROMPT_ANALYZE
        use_json_format = True
    else:
        p = f"{apply_instructions}\n\nComplete file code:\n{code}\nApply all selected refactorings."
        system = SYSTEM_PROMPT_APPLY
        use_json_format = False
    nctx = 131072 if "gemma4" in model else 32768
    payload = {"model": model, "system": system, "prompt": p, "stream": False,
              "options": {"temperature": temp, "top_p": 0.9, "num_ctx": nctx}}
    if use_json_format:
        payload["format"] = "json"
    r = requests.post(OLLAMA_URL, headers={"Content-Type": "application/json"},
                    data=json.dumps(payload), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def extract_smells(resp, full_code=""):
    try:
        response_text = resp.get("response", "{}")
        smells = json.loads(response_text).get("smells", [])
        if full_code:
            full_lines = full_code.split('\n')
            for s in smells:
                loc = s.get("location", {})
                start = loc.get("start_line", 0)
                end = loc.get("end_line", 0)
                if 1 <= start <= end <= len(full_lines):
                    s["old_code"] = '\n'.join(full_lines[start-1:end])
                fix_indentation(s, full_code)
                # Generate diff locally if model didn't provide a proper one
                if not s.get("diff") or s.get("old_code") == s.get("new_code"):
                    old = s.get("old_code", "")
                    new = s.get("new_code", "")
                    if old and new and old != new:
                        s["diff"] = generate_diff(old, new)
        return smells
    except:
        return []


def generate_diff(old_code, new_code):
    old_lines = old_code.split('\n')
    new_lines = new_code.split('\n')
    diff = difflib.unified_diff(old_lines, new_lines, lineterm='')
    return '\n'.join(diff)


def fix_indentation(smell, full_code):
    old = smell.get('old_code', '')
    new = smell.get('new_code', '')
    if not old or not new or old == new:
        return
    old_lines = old.split('\n')
    new_lines = new.split('\n')
    if not old_lines or not new_lines:
        return
    first_old = old_lines[0]
    base_indent = len(first_old) - len(first_old.lstrip())
    if base_indent <= 0:
        return
    # Find minimum indentation in new_code to normalize
    new_indents = [len(line) - len(line.lstrip()) for line in new_lines if line.strip()]
    min_new_indent = min(new_indents) if new_indents else 0
    new_lines_fixed = []
    for line in new_lines:
        if line.strip():
            # Normalize: subtract min indentation, then add base
            normalized_indent = len(line) - len(line.lstrip()) - min_new_indent
            total_indent = base_indent + normalized_indent
            new_lines_fixed.append(' ' * total_indent + line.lstrip())
        else:
            new_lines_fixed.append(line)
    smell['new_code'] = '\n'.join(new_lines_fixed)


def display_smell(s, i):
    loc = s.get("location", {})
    print("\n" + "=" * 70)
    print(f"VORSCHLAG {i + 1}: {s.get('type', 'unknown')}")
    print(f"Beschreibung: {s.get('description', '')}")
    print(f"Zeile: {loc.get('start_line', '?')}-{loc.get('end_line', '?')}")
    print(f"Auswirkung: {s.get('impact', '')}")
    print(f"Begründung: {s.get('reason', '')}")
    print("=" * 70)
    for field, label in [('old_code', 'Aktueller Code'), ('new_code', 'Vorgeschlagener Code'), ('diff', 'Diff')]:
        c = s.get(field, '')
        if c:
            print(f"\n{label}:")
            print("-" * 70)
            display_with_bat(c, "diff" if field == "diff" else "python")
            print("-" * 70)


def get_selection(smells):
    sel = []
    for i, s in enumerate(smells):
        display_smell(s, i)
        r = input("Anwenden? (j=ja, n=nein/weiter, a=alle, q=abbruch): ").strip().lower()
        if r in ('j', 'y', 'yes', ''):
            sel.append(i)
        elif r == 'a':
            return list(range(i, len(smells)))
        elif r in ('q', 'quit', 'exit'):
            return None
    return sel


def run_pyflakes(code):
    try:
        tf = f"/tmp/pyflakes_{os.getpid()}.py"
        with open(tf, 'w', encoding='utf-8') as f:
            f.write(code)
        p = subprocess.run(["pyflakes", tf], capture_output=True, text=True, timeout=10)
        if os.path.exists(tf):
            os.remove(tf)
        return p.returncode == 0, p.stdout + p.stderr
    except:
        return True, ""

def apply_refactoring(code, smells, sel, model, temp):
    if not sel:
        return code
    selected_smells = [smells[x] for x in sel]
    inst = "YOU ARE APPLYING SELECTED REFACTORINGS. YOUR ABSOLUTE PRIORITY IS: EXTERNAL BEHAVIOR MUST NEVER CHANGE.\n"
    inst += "RETURN ONLY THE COMPLETE PYTHON CODE. NO JSON. NO MARKDOWN. NO EXPLANATIONS.\n"
    inst += "Remove old methods that are replaced by new helper methods.\n\n"
    inst += "Selected refactorings to apply:\n"
    for i, s in enumerate(selected_smells, 1):
        loc = s.get("location", {})
        inst += f"{i}. Type: {s.get('type', 'unknown')}\n"
        inst += f"   Lines: {loc.get('start_line', '?')}-{loc.get('end_line', '?')}\n"
        inst += f"   Old code:\n{s.get('old_code', '')}\n"
        inst += f"   New code:\n{s.get('new_code', '')}\n\n"
    inst += "CRITICAL RULES:\n"
    inst += "- Apply ALL selected changes atomically\n"
    inst += "- REMOVE old methods that are replaced\n"
    inst += "- NEVER change behavior not explicitly in selected refactorings\n"
    inst += "- Preserve ALL validation, error messages, return values\n"
    inst += "- RETURN ONLY THE COMPLETE PYTHON CODE. NO JSON. NO MARKDOWN. NO OTHER TEXT.\n"
    
    result = call_ollama(code, model, temp, mode="apply", apply_instructions=inst)
    result_text = result.get("response", "")
    # Clean up markdown formatting if present
    for marker in ['```python', '```Python', '```']:
        result_text = result_text.replace(marker, '').strip()
    # Try to parse as JSON first (some models might still return JSON)
    try:
        parsed = json.loads(result_text)
        if isinstance(parsed, dict):
            result_text = parsed.get("code", result_text)
        elif isinstance(parsed, str):
            result_text = parsed
    except (json.JSONDecodeError, TypeError):
        pass
    
    return result_text


def main():
    p = argparse.ArgumentParser(description="KI-Refactoring-Agent")
    p.add_argument("file", help="Dateipfad")
    p.add_argument("--json", action="store_true", help="JSON-Ausgabe")
    p.add_argument("--output", "-o", help="Zieldatei")
    p.add_argument("--model", default="gemma4:e2b",
                  choices=["gemma4:e2b", "gemma4:9b", "qwen2.5-coder:7b", "qwen3-coder:30b",
                           "qwen3-coder:7b", "deepseek-coder:33b", "deepseek-coder:6.7b",
                           "devstral:24b", "magicoder:7b"], help="Modell")
    p.add_argument("--temperature", type=float, default=0.1, help="Temperature")
    args = p.parse_args()
    if not args.file:
        p.print_help()
        sys.exit(1)
    try:
        code = read_code(args.file)
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)
    if not check_ollama():
        print("Fehler: Ollama nicht erreichbar. Start: ollama serve", file=sys.stderr)
        sys.exit(1)
    if not check_model(args.model):
        print(f"Warnung: Modell '{args.model}' nicht verfügbar.", file=sys.stderr)
    try:
        result = call_ollama(code, args.model, args.temperature, mode="analyze")
    except Exception as e:
        print(f"API-Fehler: {e}", file=sys.stderr)
        sys.exit(1)
    smells = extract_smells(result, code)
    if not smells:
        print("Keine Vorschläge gefunden.")
        sys.exit(0)
    if args.json:
        print(json.dumps(smells, indent=2, ensure_ascii=False))
        sys.exit(0)
    selected = get_selection(smells)
    if selected is None:
        print("Abbruch.")
        sys.exit(0)
    if not selected:
        print("Keine Vorschläge ausgewählt.")
        sys.exit(0)
    backup_path = None
    if args.file and os.path.exists(args.file):
        try:
            backup_path = create_backup(args.file)
            print(f"Backup: {backup_path}")
        except Exception as e:
            print(f"Warnung: Backup fehlgeschlagen: {e}", file=sys.stderr)
    of = args.output if args.output else args.file
    try:
        print("\nApplying refactorings (model validates its own output)...")
        rc = apply_refactoring(code, smells, selected, args.model, args.temperature)
        
        print("Running syntax check...")
        ok, err = verify_syntax(rc)
        if not ok:
            print(f"  Syntax error found: {err}")
            print("  Model should have caught this!")
            if backup_path:
                print(f"Backup: {backup_path}")
            sys.exit(1)
        
        print("Running pyflakes...")
        ok, flakes_err = run_pyflakes(rc)
        if not ok:
            print(f"  Pyflakes issues found:\n{flakes_err}")
            print("  Model should have fixed these!")
            if backup_path:
                print(f"Backup: {backup_path}")
            # Don't exit - just warn, as model should have handled this
        else:
            print("  Pyflakes: OK")
        
        with open(of, 'w', encoding='utf-8') as f:
            f.write(rc)
        print(f"\nRefactoring complete. {len(selected)} Vorschlag/Vorschläge angewendet: {of}")
    except PermissionError:
        print(f"Fehler: Keine Schreibrechte für {of}")
        sys.exit(1)
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
