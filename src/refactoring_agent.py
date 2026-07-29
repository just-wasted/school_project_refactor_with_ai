#!/usr/bin/env python3
"""KI-Refactoring-Agent - CLI-Tool für Code-Analyse via Ollama-API."""

import argparse
import sys
import json
import os
import subprocess
import requests
import difflib
import shutil

OLLAMA_API_URL = "http://localhost:11434/api/generate"
TIMEOUT = 120

# Lade System-Prompt aus externer Datei für bessere Wartbarkeit
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
SYSTEM_PROMPT_FILE = os.path.join(PROMPTS_DIR, "system_prompt.md")


def load_system_prompt():
    """Lade den System-Prompt aus der Markdown-Datei."""
    try:
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback-Prompt falls Datei nicht gefunden
        return """Du bist ein spezialisierter Refactoring-Agent mit der einzigen Aufgabe,
Code zu analysieren und konkrete Refactoring-Vorschläge als JSON zu generieren.
Erkenne: Duplikate, lange Methoden (>20 Zeilen), unklare Namen, gemischte Verantwortlichkeiten,
hohes zyklomatische Komplexität, unnötige Kommentare, Magic Numbers/Strings, zu viele Parameter (>4).
Ausgabeformat: {"file":"...","language":"...","smells":[{"type":"...","location":{"file":"...","start_line":N,"end_line":N},
"description":"...","severity":"high|medium|low","suggestion":"<full_refactored_code>...<full_refactored_code>","reason":"...","impact":"readability|maintainability|testability|performance"}],
"stats":{"total_smells":N,"high":N,"medium":N,"low":N,"coverage":"X%"}}
Regeln: 
1. Sei präzise, gib vollständige Code-Beispiele im suggestion Feld als ```python...``` Block
2. Ersetze den betroffenen Code komplett im suggestion Feld
3. Erkläre Begründungen kurz
4. Ändere kein Verhalten
5. Gib immer den vollständigen refactored Code zurück, nicht nur Beschreibungen"""


SYSTEM_PROMPT = load_system_prompt()


def has_bat():
    """Prüfe ob bat installiert ist."""
    return shutil.which("bat") is not None


def display_diff_with_bat(diff_text):
    """Zeige den Diff mit bat für Syntax-Highlighting."""
    try:
        # bat mit Diff-Highlighting, erzwinge Farben und keine Decorationen wie Zeilennummern
        process = subprocess.Popen(
            ["bat", "--paging=never", "--color=always", "--decorations=never", "--language=diff"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=diff_text, timeout=5)
        if process.returncode == 0:
            print(stdout, end='')
        else:
            # Falls bat fehlschlägt, normale Ausgabe
            print(diff_text, end='')
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # bat nicht verfügbar oder Fehler
        print(diff_text, end='')


def read_code(file_path):
    """Read code from file or stdin."""
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, PermissionError) as e:
            raise RuntimeError(f"Dateifehler: {e}")
    return sys.stdin.read()


def check_ollama():
    """Check if Ollama server is available."""
    try:
        requests.get("http://localhost:11434/api/tags", timeout=10)
        return True
    except requests.exceptions.RequestException:
        return False


def check_model(model):
    """Check if model is available on Ollama."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        models = [m["name"] for m in response.json().get("models", [])]
        return model in models
    except requests.exceptions.RequestException:
        return False


def call_ollama(code, model, temperature):
    """Call Ollama API with system prompt and code."""
    payload = {
        "model": model,
        "system": SYSTEM_PROMPT,
        "prompt": f"Analysiere den folgenden Code:\n\n```\n{code}\n```",
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature, "top_p": 0.9}
    }
    try:
        response = requests.post(
            OLLAMA_API_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama API Error: {e}") from e


def format_output(response, output_format):
    """Format output as JSON or text."""
    if output_format == "json":
        return json.dumps(response, indent=2, ensure_ascii=False)
    result = response.get("response", "{}")
    try:
        data = json.loads(result)
        output = []
        for smell in data.get("smells", []):
            loc = smell.get("location", {})
            output.append(
                f"{smell.get('type', 'unknown')}: "
                f"Zeile {loc.get('start_line', '?')}-{loc.get('end_line', '?')}\n"
                f"  {smell.get('description', '')}\n"
                f"  Vorschlag: {smell.get('suggestion', '')}\n"
                "-" * 60
            )
        return "\n".join(output)
    except json.JSONDecodeError:
        return result


def extract_smells(response):
    """Extrahiere Smells aus der Ollama-Antwort."""
    result = response.get("response", "{}")
    try:
        data = json.loads(result)
        return data.get("smells", [])
    except json.JSONDecodeError:
        return []


def extract_code_blocks(text):
    """Extrahiere Code-Blöcke aus Text (z. B. aus KI-Vorschlägen)."""
    import re
    # Finde Code in ```...``` Blöcken (auch mit Language-Specifier wie ```python)
    code_blocks = re.findall(r'```(?:\w*\n)?(.*?)```', text, re.DOTALL)
    if code_blocks:
        return [block.strip() for block in code_blocks]
    return []


def show_diff(original, modified, smell):
    """Zeige den Diff zwischen Original und modifiziertem Code."""
    lines = original.split('\n')
    start_line = smell.get('location', {}).get('start_line', 1) - 1
    end_line = smell.get('location', {}).get('end_line', 1) - 1
    
    print("\n" + "=" * 70)
    print(f"VORSCHLAG: {smell.get('type', 'unknown')}")
    print(f"Beschreibung: {smell.get('description', '')}")
    print(f"Zeile: {smell.get('location', {}).get('start_line', '?')}-{smell.get('location', {}).get('end_line', '?')}")
    print(f"Auswirkung: {smell.get('impact', 'unknown')}")
    print(f"Begründung: {smell.get('reason', '')}")
    print("=" * 70)
    
    # Zeige den betroffenen Code-Bereich mit absoluten Zeilennummern
    if start_line >= 0 and end_line < len(lines):
        print("\nAktueller Code:")
        print("-" * 70)
        
        # Zeige nur die Zeilen im Bereich start_line bis end_line
        for i in range(start_line, end_line + 1):
            if i < len(lines):
                # Absolute Zeilennummer (i+1 weil lines 0-indexed ist)
                print(f"{i+1:4d}: {lines[i]}")
        print("-" * 70)
    
    # Zeige die Vorschläge
    suggestion = smell.get('suggestion', '')
    if suggestion:
        print("\nVorgeschlagene Lösung:")
        print("-" * 70)
        
        # Versuche Code-Blöcke zu extrahieren
        code_blocks = extract_code_blocks(suggestion)
        if code_blocks:
            for i, block in enumerate(code_blocks, 1):
                print(f"Code-Beispiel {i}:")
                for line in block.strip().split('\n'):
                    if line.strip():
                        print(f"    {line}")
                print()
        else:
            # Kein Code-Beispiel, nur Beschreibung
            print(f"Hinweis: {suggestion}")
        print("-" * 70)
    
    # Zeige was tatsächlich geändert wird
    if modified != original:
        print("\nÄnderungen (Diff):")
        print("-" * 70)
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile="original",
            tofile="modified",
            lineterm="",
            n=0
        )
        # Generiere den Diff als String
        diff_lines = []
        for line in diff:
            if line.startswith('+++') or line.startswith('---'):
                continue
            diff_lines.append(line)
        
        diff_text = ''.join(diff_lines)
        
        # Verwende bat für farbige Ausgabe, falls verfügbar
        if has_bat():
            display_diff_with_bat(diff_text)
        else:
            # Manuelle Farbausgabe mit ANSI-Codes
            for line in diff_lines:
                if line.startswith('@@'):
                    print(f" {line}", end='')
                elif line.startswith('+') and not line.startswith('++'):
                    print(f"\033[32m{line}\033[0m", end='')
                elif line.startswith('-') and not line.startswith('--'):
                    print(f"\033[31m{line}\033[0m", end='')
                else:
                    print(f" {line}", end='')
        print("-" * 70)


def apply_smell(code, smell):
    """Wendet einen einzelnen Smell-Vorschlag auf den Code an."""
    lines = code.split('\n')
    start_line = smell.get('location', {}).get('start_line', 1) - 1
    end_line = smell.get('location', {}).get('end_line', 1) - 1
    
    suggestion = smell.get('suggestion', '')
    
    # Extrahiere Code-Blöcke aus dem suggestion
    code_blocks = extract_code_blocks(suggestion)
    
    if start_line >= 0 and end_line < len(lines) and code_blocks:
        # Ersetze den betroffenen Bereich mit dem refactored Code
        refactored_code = code_blocks[0]
        
        # Ersetze die Zeilen von start_line bis end_line
        new_lines = lines[:start_line] + [refactored_code] + lines[end_line + 1:]
        return '\n'.join(new_lines)
    elif start_line >= 0 and end_line < len(lines):
        # Falls kein Code-Block im suggestion, füge Kommentar ein
        lines[start_line] = f"# REFACCTORING: {smell.get('description', '')}\n# {suggestion}\n" + lines[start_line]
        return '\n'.join(lines)
    
    return code + f"\n\n# REFACCTORING: {smell.get('description', '')}\n# {suggestion}\n"


def apply_interactive(code, smells, output_file=None):
    """Interaktiver Modus: Zeigt jeden Smell an und fragt nach Bestätigung."""
    if not smells:
        print("Keine Refactoring-Vorschläge gefunden.")
        return code
    
    modified_code = code
    applied_count = 0
    
    for smell in smells:
        proposed_code = apply_smell(modified_code, smell)
        show_diff(modified_code, proposed_code, smell)
        
        while True:
            response = input("Anwenden? (j=ja, n=nein/weiter, a=alle, q=abbruch): ").strip().lower()
            if response in ('j', 'y', 'yes', ''):
                modified_code = proposed_code
                applied_count += 1
                break
            elif response in ('n', 'no'):
                break
            elif response in ('a', 'all'):
                modified_code = proposed_code
                applied_count += 1
                for remaining_smell in smells[smells.index(smell) + 1:]:
                    modified_code = apply_smell(modified_code, remaining_smell)
                    applied_count += 1
                break
            elif response in ('q', 'quit', 'exit'):
                print("Abbruch.")
                return None
            else:
                print("Ungültige Eingabe. Bitte j/n/a/q eingeben.")
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(modified_code)
        print(f"\nRefactoring abgeschlossen. {applied_count} Vorschläge angewendet.")
        print(f"Ergebnis geschrieben nach: {output_file}")
    
    return modified_code


def apply_all(code, smells, output_file):
    """Wendet alle Smell-Vorschläge automatisch an."""
    if not smells:
        raise RuntimeError("Keine Refactoring-Vorschläge gefunden")
    
    modified_code = code
    for smell in smells:
        modified_code = apply_smell(modified_code, smell)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(modified_code)
    
    return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="KI-Refactoring-Agent für Code-Analyse und Refactoring"
    )
    parser.add_argument("file", help="Dateipfad der zu analysierenden/processenden Datei")
    parser.add_argument(
        "--json", action="store_true", help="Nur JSON-Ausgabe der Vorschläge (kein Apply)"
    )
    parser.add_argument(
        "--auto-apply", action="store_true", 
        help="Alle Vorschläge automatisch anwenden (ohne Nachfrage)"
    )
    parser.add_argument(
        "--output", "-o", 
        help="Zieldatei für refaktorierten Code (optional, Standard: Originaldatei überscheiben)"
    )
    parser.add_argument(
        "--model", default="qwen2.5-coder:7b",
        choices=["qwen2.5-coder:7b", "qwen3-coder:30b", "qwen3-coder:7b", 
                 "deepseek-coder:33b", "deepseek-coder:6.7b", 
                 "devstral:24b", "magicoder:7b"],
        help="Ollama-Modell (default: qwen2.5-coder:7b)"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.1, help="Kreativität (0.0-1.0)"
    )
    
    args = parser.parse_args()

    if not args.file:
        parser.print_help()
        sys.exit(1)

    try:
        code = read_code(args.file)
    except RuntimeError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)

    if not check_ollama():
        print(
            "Fehler: Ollama-Server nicht erreichbar.\n"
            "Installation: curl -fsSL https://ollama.com/install.sh | sh\n"
            "Start: ollama serve",
            file=sys.stderr
        )
        sys.exit(1)

    if not check_model(args.model):
        print(f"Warnung: Modell '{args.model}' nicht verfügbar.", file=sys.stderr)

    try:
        result = call_ollama(code, args.model, args.temperature)
    except RuntimeError as e:
        print(f"API-Fehler: {e}", file=sys.stderr)
        sys.exit(1)

    smells = extract_smells(result)
    if not smells:
        print("Keine Refactoring-Vorschläge gefunden.")
        sys.exit(0)

    if args.json:
        print(format_output(result, "json"))
    elif args.auto_apply:
        output_file = args.output if args.output else args.file
        try:
            apply_all(code, smells, output_file)
            print(f"Alle {len(smells)} Vorschläge automatisch angewendet.")
            print(f"Ergebnis geschrieben nach: {output_file}")
        except RuntimeError as e:
            print(f"Fehler: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        output_file = args.output if args.output else args.file
        try:
            apply_interactive(code, smells, output_file)
        except RuntimeError as e:
            print(f"Fehler: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
