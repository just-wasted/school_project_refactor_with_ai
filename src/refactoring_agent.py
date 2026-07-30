#!/usr/bin/env python3
"""KI-Refactoring-Agent - Dünnes Interface für Code-Refactoring via Ollama."""

import argparse, json, os, subprocess, sys, shutil, datetime, requests, difflib

OLLAMA_URL = "http://localhost:11434/api/generate"
TIMEOUT = 240
BACKUP_DIR = "backup"

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
with open(os.path.join(PROMPTS_DIR, "system_prompt_apply.md"), "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_APPLY = f.read().strip()

# Smell-type specific analyze prompts
SMELL_TYPES = ["Long Method", "Duplicate Code", "Magic Numbers", "Unclear Names", "Too Many Parameters"]
SYSTEM_PROMPT_ANALYZE = {}
for st in SMELL_TYPES:
    try:
        with open(os.path.join(PROMPTS_DIR, f"system_prompt_analyze_{st.lower().replace(' ', '_')}.md"), "r", encoding="utf-8") as f:
            SYSTEM_PROMPT_ANALYZE[st] = f.read().strip()
    except FileNotFoundError:
        SYSTEM_PROMPT_ANALYZE[st] = ""


def create_backup(fp):
    src_dir = os.path.dirname(os.path.abspath(__file__))
    pr = os.path.dirname(src_dir)
    for bd in [os.path.join(pr, BACKUP_DIR), os.path.join("/tmp", BACKUP_DIR)]:
        try:
            os.makedirs(bd, exist_ok=True)
            break
        except:
            pass
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    rp = os.path.relpath(fp, pr)
    bp = os.path.join(bd, f"{ts}_{rp.replace('/', '_').replace(chr(92), '_')}")
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
        print(out if p.returncode == 0 else text)
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


def call_ollama(code, model, temp, mode="analyze", apply_instructions="", smell_type=None):
    nctx = 131072 if "gemma4" in model else 32768
    n_predict = 16384 if "gemma4" in model else 8192
    if smell_type == "Long Method":
        n_predict = 32768 if "gemma4" in model else 16384
    if mode == "analyze":
        p = f"Here is the COMPLETE Python file:\n\n```\n{code}\n```\n\nAnalyze and return code smells with old_code, new_code, and diff."
        system = SYSTEM_PROMPT_ANALYZE.get(smell_type, SYSTEM_PROMPT_ANALYZE.get(SMELL_TYPES[0], "")) if smell_type else ""
        if not system:
            system = "You are a senior Python code refactoring specialist. Find code smells and return them in JSON."
        payload = {"model": model, "system": system, "prompt": p, "stream": False,
                  "options": {"temperature": temp, "top_p": 0.9, "num_ctx": nctx, "num_predict": n_predict}}
    else:
        p = f"{apply_instructions}\n\nComplete file code:\n{code}\nApply all selected refactorings."
        system = SYSTEM_PROMPT_APPLY
        payload = {"model": model, "system": system, "prompt": p, "stream": False,
                  "options": {"temperature": temp, "top_p": 0.9, "num_ctx": nctx, "num_predict": n_predict}}
    r = requests.post(OLLAMA_URL, headers={"Content-Type": "application/json"},
                    data=json.dumps(payload), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def fix_truncated_json(t):
    if not t.strip():
        return "{}"
    in_s = False
    esc = False
    for i in range(len(t) - 1, -1, -1):
        c = t[i]
        if esc:
            esc = False
            continue
        if c == '\\':
            esc = True
            continue
        if c == '"':
            in_s = not in_s
        if not in_s and c == '}':
            return t[:i + 1]
    return "{}"


def generate_diff(old_code, new_code):
    return '\n'.join(difflib.unified_diff(old_code.split('\n'), new_code.split('\n'), lineterm=''))


def deduplicate_smells(smells):
    """Remove duplicate smells based on type and location."""
    seen = set()
    unique = []
    for s in smells:
        loc = s.get("location", {})
        key = (s.get("type", ""), loc.get("start_line", 0), loc.get("end_line", 0))
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def extract_smells(resp, full_code=""):
    try:
        rt = resp.get("response", "{}")
        if rt.strip():
            # Remove markdown code blocks (```json ... ```)
            import re
            rt = re.sub(r'```(?:json|python|Python)?', '', rt).strip()
            rt = re.sub(r'```', '', rt).strip()
            try:
                parsed = json.loads(rt)
            except:
                rt = fix_truncated_json(rt)
                parsed = json.loads(rt)
        else:
            parsed = {}
        smells = parsed if isinstance(parsed, list) else parsed.get("smells", [])
        for s in smells:
            for field in ['old_code', 'new_code', 'diff']:
                if field in s:
                    for m in ['```python', '```Python', '```']:
                        s[field] = s[field].replace(m, '').strip()
        if full_code:
            fl = full_code.split('\n')
            for s in smells:
                loc = s.get("location", {})
                st = loc.get("start_line", 0)
                en = loc.get("end_line", 0)
                if 1 <= st <= en <= len(fl):
                    s["old_code"] = '\n'.join(fl[st-1:en])
                fix_indentation(s, full_code)
                if not s.get("diff") or s.get("old_code") == s.get("new_code"):
                    old = s.get("old_code", "")
                    new = s.get("new_code", "")
                    if old and new and old != new:
                        s["diff"] = generate_diff(old, new)
        return smells
    except:
        return []


def fix_indentation(smell, full_code):
    old = smell.get('old_code', '')
    new = smell.get('new_code', '')
    if not old or not new or old == new:
        return
    ol = old.split('\n')
    nl = new.split('\n')
    if not ol or not nl:
        return
    base = len(ol[0]) - len(ol[0].lstrip())
    if base <= 0:
        return
    mins = min([len(l) - len(l.lstrip()) for l in nl if l.strip()] or [0])
    nlf = []
    for line in nl:
        if line.strip():
            nlf.append(' ' * (base + len(line) - len(line.lstrip()) - mins) + line.lstrip())
        else:
            nlf.append(line)
    smell['new_code'] = '\n'.join(nlf)


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
    ss = [smells[x] for x in sel]
    inst = "YOU ARE APPLYING SELECTED REFACTORINGS TO THE COMPLETE FILE BELOW.\n"
    inst += "YOUR ABSOLUTE PRIORITIES: (1) EXTERNAL BEHAVIOR MUST BE 100% IDENTICAL, (2) DELETE ALL OLD CODE THAT IS REPLACED.\n"
    inst += "RETURN ONLY THE COMPLETE PYTHON FILE CODE. NO JSON. NO MARKDOWN. NO EXPLANATIONS. NO COMMENTS.\n\n"
    
    inst += "REFACTORINGS TO APPLY:\n"
    for i, s in enumerate(ss, 1):
        loc = s.get("location", {})
        old_code = s.get('old_code', '').strip()
        new_code = s.get('new_code', '').strip()
        inst += f"--- Refactoring {i}: {s.get('type', 'unknown')} (Lines {loc.get('start_line', '?')}-{loc.get('end_line', '?')}) ---\n"
        inst += f"OLD CODE TO REMOVE:\n{old_code}\n\n"
        inst += f"NEW CODE TO INSERT:\n{new_code}\n\n"
    
    inst += "\nCRITICAL INSTRUCTIONS:\n"
    inst += "- DELETE all old_code blocks EXACTLY as shown above\n"
    inst += "- INSERT all new_code blocks EXACTLY as shown above\n"
    inst += "- If new_code contains helper methods: insert at appropriate location, DELETE replaced old methods\n"
    inst += "- UPDATE ALL call sites throughout the entire file to use new method/parameter names\n"
    inst += "- PRESERVE: exact behavior, validation, error messages, return values, side effects\n"
    inst += "- NEVER leave old code commented out or in place\n"
    inst += "- File MUST be valid Python - check before returning\n"
    inst += "- RETURN ONLY THE CODE - nothing else\n\n"
    
    result = call_ollama(code, model, temp, mode="apply", apply_instructions=inst)
    rt = result.get("response", "")
    for m in ['```python', '```Python', '```']:
        rt = rt.replace(m, '').strip()
    try:
        parsed = json.loads(rt)
        rt = parsed.get("code", rt) if isinstance(parsed, dict) else (parsed if isinstance(parsed, str) else rt)
    except:
        pass
    return rt


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
    
    # Analyze each smell type separately and aggregate results
    all_smells = []
    print("Analyzing for each smell type...")
    for st in SMELL_TYPES:
        print(f"  Checking: {st}...", end=" ", flush=True)
        try:
            result = call_ollama(code, args.model, args.temperature, mode="analyze", smell_type=st)
            smells = extract_smells(result, code)
            if smells:
                print(f"Found {len(smells)} smell(s)")
            else:
                print("None")
            all_smells.extend(smells)
        except Exception as e:
            print(f"Error: {e}")
    
    # Deduplicate smells
    all_smells = deduplicate_smells(all_smells)
    
    if not all_smells:
        print("Keine Vorschläge gefunden.")
        sys.exit(0)
    
    print(f"Total: {len(all_smells)} unique smell(s) found.")
    smells = all_smells
    if not smells:
        print("Keine Vorschläge gefunden.")
        sys.exit(0)
    if args.json:
        print(json.dumps({"smells": smells}, indent=2, ensure_ascii=False))
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
        ok, fe = run_pyflakes(rc)
        if not ok:
            print(f"  Pyflakes issues found:\n{fe}")
            print("  Model should have fixed these!")
            if backup_path:
                print(f"Backup: {backup_path}")
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
