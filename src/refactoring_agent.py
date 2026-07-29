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
import datetime

OLLAMA_API_URL = "http://localhost:11434/api/generate"
TIMEOUT = 240
BACKUP_DIR = "backup"

# Lade System-Prompt aus externer Datei für bessere Wartbarkeit
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
SYSTEM_PROMPT_FILE = os.path.join(PROMPTS_DIR, "system_prompt.md")


def load_system_prompt():
    """Lade den System-Prompt aus der Markdown-Datei."""
    try:
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(
            f"System-Prompt-Datei nicht gefunden: {SYSTEM_PROMPT_FILE}\n"
            "Bitte stelle sicher, dass die Datei src/prompts/system_prompt.md existiert."
        )


SYSTEM_PROMPT = load_system_prompt()


def create_backup(file_path):
    """Erstelle nur-lesbare Backup-Kopie der Originaldatei.
    
    Backups werden im Projekt-Root-Verzeichnis (neben src/) gespeichert,
    um Berechtigungsprobleme mit nur-lesbaren Quelldateien zu vermeiden.
    """
    # Verwende das Parent-Verzeichnis von src/ als Backup-Root
    # Annahme: file_path ist z.B. code_smells/service.py
    # Projekt-Root ist dann: os.path.dirname(os.path.dirname(src/))
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    backup_dir = os.path.join(project_root, BACKUP_DIR)
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
    except PermissionError:
        # Falls auch Projekt-Root kein Schreibrecht hat, verwende /tmp
        backup_dir = os.path.join("/tmp", BACKUP_DIR)
        os.makedirs(backup_dir, exist_ok=True)
    
    # Erzeuge einen einzigartigen Dateinamen mit Timestamp und relativem Pfad
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    rel_path = os.path.relpath(file_path, project_root)
    # Ersetze Verzeichnis-Trenner für Dateinamen
    safe_rel_path = rel_path.replace("/", "_").replace("\\", "_")
    backup_filename = f"{timestamp}_{safe_rel_path}"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    shutil.copy2(file_path, backup_path)
    os.chmod(backup_path, 0o444)
    return backup_path


def verify_syntax(code):
    """Prüfe ob Code syntaktisch gültig ist mit py_compile."""
    try:
        temp_file = f"/tmp/syntax_check_{os.getpid()}.py"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        result = subprocess.run(
            ["python", "-m", "py_compile", temp_file],
            capture_output=True,
            timeout=5
        )
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return result.returncode == 0, result.stderr.decode() if result.stderr else ""
    except Exception as e:
        return False, str(e)


def has_bat():
    """Prüfe ob bat installiert ist."""
    return shutil.which("bat") is not None


def display_code_with_bat(code_text, language="python"):
    """Zeige Code mit bat für Syntax-Highlighting."""
    try:
        process = subprocess.Popen(
            ["bat", "--paging=never", "--color=always", "--decorations=never", f"--language={language}"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=code_text, timeout=5)
        if process.returncode == 0:
            print(stdout, end='')
        else:
            print(code_text)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        print(code_text)


def display_diff_with_bat(diff_text):
    """Zeige den Diff mit bat für Syntax-Highlighting."""
    display_code_with_bat(diff_text, language="diff")


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


def call_ollama(code, model, temperature, error_context=None):
    """Call Ollama API with system prompt and code."""
    # Füge Zeilennummern zum Code hinzu
    lines = code.split('\n')
    numbered_code = ''
    for i, line in enumerate(lines, 1):
        numbered_code += f"{i:4d}: {line}\n"
    
    prompt = f"Analysiere den folgenden Code MIT ZEILENNUMMERN. Verwende DIESE NUMMERN für start_line und end_line.\n\n```\n{numbered_code}\n```"
    
    if error_context:
        # Extrahiere nur den relevanten Fehlertext, entferne Dateipfade und technische Details
        clean_error = error_context.split('syntax_check_')[0].split('Finaler Code hat Syntax-Fehler:')[-1].strip()
        prompt += f"\n\nFEHLERHINWEIS: {clean_error}\nBitte korrigiere deine Code-Vorschläge so, dass sie syntaktisch gültigen Python-Code erzeugen."
    
    # Setze Kontextfenster basierend auf dem Modell
    # gemma4:e2b unterstützt 128K Token (131072), qwen2.5-coder:7b unterstützt 32K
    if "gemma4" in model:
        num_ctx = 131072  # 128K für Gemma4
    else:
        num_ctx = 32768  # 32K für andere Modelle (qwen, deepseek, etc.)
    
    payload = {
        "model": model,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature, "top_p": 0.9, "num_ctx": num_ctx}
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
    
    # Korrigiere falls start_line > end_line (Einfügung)
    if start_line > end_line:
        start_line = end_line
    
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
        
        # Für Einfügungen (start_line == end_line) - zeige Kontext um die Einfügestelle
        if start_line == end_line:
            # Zeige 2 Zeilen Kontext vor und nach der Einfügestelle
            context_start = max(0, start_line - 2)
            context_end = min(len(lines) - 1, start_line + 2)
            
            current_code = []
            for i in range(context_start, context_end + 1):
                marker = ">>> " if i == start_line else "    "
                current_code.append(f"{marker}{i+1:4d}: {lines[i]}")
            
            if has_bat():
                display_code_with_bat('\n'.join(current_code), language="python")
            else:
                for line in current_code:
                    print(line)
        else:
            # Für Ersatz - zeige nur die Zeilen im Location-Bereich
            current_code = []
            for i in range(start_line, end_line + 1):
                if i < len(lines):
                    current_code.append(f"{i+1:4d}: {lines[i]}")
            
            if has_bat():
                display_code_with_bat('\n'.join(current_code), language="python")
            else:
                for line in current_code:
                    print(line)
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
                if has_bat():
                    display_code_with_bat(block.strip(), language="python")
                else:
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
            n=3
        )
        # Generiere den Diff als String mit Zeilenumbrüchen
        diff_lines = []
        for line in diff:
            # Behalte --- und +++ Zeilen für korrekten unified diff
            # Entferne nur die Dateinamen
            if line.startswith('--- ') or line.startswith('+++ '):
                # Ersetze Dateinamen mit generischen Namen
                if line.startswith('--- '):
                    diff_lines.append('--- original')
                else:
                    diff_lines.append('+++ modified')
            else:
                diff_lines.append(line.rstrip('\n'))
        
        diff_text = '\n'.join(diff_lines)
        
        # Verwende bat für farbige Ausgabe, falls verfügbar
        if has_bat():
            display_diff_with_bat(diff_text)
        else:
            # Manuelle Farbausgabe mit ANSI-Codes
            for line in diff_lines:
                if line.startswith('@@'):
                    print(f" {line}")
                elif line.startswith('+') and not line.startswith('++'):
                    print(f"\033[32m{line}\033[0m")
                elif line.startswith('-') and not line.startswith('--'):
                    print(f"\033[31m{line}\033[0m")
                else:
                    print(f" {line}")
        print("-" * 70)


def apply_interactive_finalize(modified_code, applied_count, output_file, backup_path=None):
    """Hilfsfunktion zum Abschließen des interaktiven Modus."""
    # Syntax-Prüfung des finalen Codes
    is_valid, error = verify_syntax(modified_code)
    if not is_valid:
        print(f"\nFehler: Finaler Code hat Syntax-Fehler: {error}")
        if backup_path:
            print(f"Backup: {backup_path}")
        return None
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(modified_code)
            print(f"\nRefactoring abgeschlossen. {applied_count} Vorschlaege angewendet.")
            print(f"Ergebnis geschrieben nach: {output_file}")
        except PermissionError:
            print(f"\nFehler: Keine Schreibrechte fuer {output_file}")
            print("Bitte waehle einen anderen Ausgabepfad oder aendere die Berechtigungen.")
            return None
    return modified_code


def apply_smell(code, smell):
    """Wendet einen einzelnen Smell-Vorschlag auf den Code an.
    
    Ersetzt den Code im Location-Bereich (start_line bis end_line) durch den suggestion-Code
    oder fügt neuen Code ein, wenn start_line == end_line (Einfügung).
    
    Args:
        code: Originaler Code
        smell: Smell-Vorschlag mit location und suggestion
    
    Returns:
        modifizierter Code
    """
    lines = code.split('\n')
    start_line = smell.get('location', {}).get('start_line', 1) - 1
    end_line = smell.get('location', {}).get('end_line', 1) - 1
    
    suggestion = smell.get('suggestion', '')
    
    # Extrahiere Code-Blöcke aus dem suggestion
    code_blocks = extract_code_blocks(suggestion)
    
    # Falls start_line > end_line, korrigiere zu Einfügung nach end_line
    if start_line > end_line:
        start_line = end_line
    
    # Hole den tatsächlichen Code aus dem suggestion
    if code_blocks:
        refactored_code = code_blocks[0].strip()
    else:
        # Falls kein Code-Block gefunden wurde, überspringe diesen Vorschlag
        # (vermutlich ist es nur eine Beschreibung ohne Code)
        return code
    
    # Einfacher Ersatz ohne Einrückungskorrektur - das Modell muss es richtig machen
    # Fall 1: Einfügung (start_line == end_line)
    if start_line == end_line:
        # Füge nach der Zeile start_line ein
        if start_line >= 0 and start_line <= len(lines):
            new_lines = lines[:start_line + 1] + [refactored_code] + lines[start_line + 1:]
            proposed_code = '\n'.join(new_lines)
        else:
            # Einfügung am Anfang
            proposed_code = refactored_code + '\n' + code
    
    # Fall 2: Ersatz (start_line < end_line)
    elif start_line >= 0 and end_line < len(lines):
        # Ersetze den Code von start_line bis end_line durch den refactored_code
        new_lines = lines[:start_line] + [refactored_code] + lines[end_line + 1:]
        proposed_code = '\n'.join(new_lines)
    
    # Fall 3: Location außerhalb des Codes - füge am Ende hinzu
    else:
        proposed_code = code + '\n' + refactored_code
    
    return proposed_code


def apply_interactive(code, smells, output_file=None, file_path=None):
    """Interaktiver Modus: Zeigt jeden Smell an und fragt nach Bestätigung.
    
    Args:
        code: Originaler Code
        smells: Liste der Smell-Vorschläge
        output_file: Zieldatei für das Ergebnis
        file_path: Originaldateipfad (für Backup)
    """
    if not smells:
        print("Keine Refactoring-Vorschläge gefunden.")
        return code
    
    # Backup erstellen, wenn wir eine Datei bearbeiten
    backup_path = None
    if file_path and os.path.exists(file_path):
        backup_path = create_backup(file_path)
        print(f"Backup erstellt: {backup_path}")
    
    modified_code = code
    applied_count = 0
    
    for i, smell in enumerate(smells):
        proposed_code = apply_smell(modified_code, smell)
        
        # Wenn sich nichts geändert hat (Syntax-Fehler), überspringen
        if proposed_code == modified_code:
            continue
        
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
                # Wende aktuellen Vorschlag an
                modified_code = proposed_code
                applied_count += 1
                # Wende alle verbleibenden Vorschläge an
                for remaining_smell in smells[i + 1:]:
                    proposed = apply_smell(modified_code, remaining_smell)
                    if proposed != modified_code:
                        modified_code = proposed
                        applied_count += 1
                # Beende die Schleife
                return apply_interactive_finalize(modified_code, applied_count, output_file, backup_path)
            elif response in ('q', 'quit', 'exit'):
                print("Abbruch.")
                return None
            else:
                print("Ungültige Eingabe. Bitte j/n/a/q eingeben.")
    
    return apply_interactive_finalize(modified_code, applied_count, output_file, backup_path)


def apply_all(code, smells, output_file, file_path=None):
    """Wendet alle Smell-Vorschläge automatisch an.
    
    Args:
        code: Originaler Code
        smells: Liste der Smell-Vorschläge
        output_file: Zieldatei für das Ergebnis
        file_path: Originaldateipfad (für Backup)
    """
    if not smells:
        raise RuntimeError("Keine Refactoring-Vorschläge gefunden")
    
    # Backup erstellen
    backup_path = None
    if file_path and os.path.exists(file_path):
        backup_path = create_backup(file_path)
        print(f"Backup erstellt: {backup_path}")
    
    modified_code = code
    applied_count = 0
    
    for smell in smells:
        proposed_code = apply_smell(modified_code, smell)
        if proposed_code != modified_code:
            modified_code = proposed_code
            applied_count += 1
    
    # Syntax-Prüfung des finalen Codes
    is_valid, error = verify_syntax(modified_code)
    if not is_valid:
        print(f"Fehler: Finaler Code hat Syntax-Fehler: {error}")
        print(f"Backup: {backup_path}")
        raise RuntimeError("Finaler Code ist nicht syntaktisch gueltig")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(modified_code)
        print(f"Alle {applied_count} von {len(smells)} Vorschlaegen erfolgreich angewendet.")
        return applied_count
    except PermissionError:
        print(f"Fehler: Keine Schreibrechte fuer {output_file}")
        print("Bitte waehle einen anderen Ausgabepfad oder aendere die Berechtigungen.")
        raise RuntimeError(f"Permission denied: {output_file}")


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
        "--model", default="gemma4:e2b",
        choices=["gemma4:e2b", "gemma4:9b", "qwen2.5-coder:7b", "qwen3-coder:30b", "qwen3-coder:7b", 
                 "deepseek-coder:33b", "deepseek-coder:6.7b", 
                 "devstral:24b", "magicoder:7b"],
        help="Ollama-Modell (default: gemma4:e2b)"
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

    max_retries = 3
    retry_count = 0
    all_skipped = False
    last_error = None
    
    while retry_count < max_retries:
        try:
            result = call_ollama(code, args.model, args.temperature, last_error)
        except RuntimeError as e:
            print(f"API-Fehler: {e}", file=sys.stderr)
            sys.exit(1)

        smells = extract_smells(result)
        if not smells:
            print("Keine Refactoring-Vorschläge gefunden.")
            sys.exit(0)

        if args.json:
            print(format_output(result, "json"))
            break
        elif args.auto_apply:
            output_file = args.output if args.output else args.file
            try:
                applied_count = apply_all(code, smells, output_file, file_path=args.file)
                # Pruefe ob alle Vorschlaege uebersprungen wurden
                if applied_count == 0:
                    all_skipped = True
                    last_error = "Alle Vorschlaege wurden uebersprungen (Syntax-Fehler in jeder Aenderung)"
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"Alle Vorschlaege hatten Syntax-Fehler. Versuche es nochmal ({retry_count}/{max_retries})...")
                        continue
                    else:
                        print(f"Alle {max_retries} Versuche fehlgeschlagen. Alle Vorschlaege hatten Syntax-Fehler.")
                        print("Bitte pruefe die KI-Antworten oder passe den System-Prompt an.")
                        sys.exit(1)
                break
            except RuntimeError as e:
                # Syntax-Fehler im finalen Code - retry
                last_error = str(e)
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Fehler: {e}")
                    print(f"Versuche es nochmal ({retry_count}/{max_retries})...")
                    continue
                else:
                    print(f"Fehler: {e}")
                    print(f"Alle {max_retries} Versuche fehlgeschlagen.")
                    sys.exit(1)
        else:
            output_file = args.output if args.output else args.file
            try:
                result_code = apply_interactive(code, smells, output_file, file_path=args.file)
                if result_code is None:
                    # User cancelled or all suggestions skipped
                    all_skipped = True
                    last_error = "Interaktive Anwendung wurde abgebrochen oder alle Vorschlaege uebersprungen"
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"Alle Vorschlaege hatten Probleme. Versuche es nochmal ({retry_count}/{max_retries})...")
                        continue
                    else:
                        print(f"Alle {max_retries} Versuche fehlgeschlagen.")
                        sys.exit(1)
                break
            except RuntimeError as e:
                # Permission error or other - retry
                last_error = str(e)
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Fehler: {e}")
                    print(f"Versuche es nochmal ({retry_count}/{max_retries})...")
                    continue
                else:
                    print(f"Fehler: {e}")
                    print(f"Alle {max_retries} Versuche fehlgeschlagen.")
                    sys.exit(1)
    
    if retry_count >= max_retries and all_skipped:
        print(f"Alle {max_retries} Versuche fehlgeschlagen.")
        sys.exit(1)


if __name__ == "__main__":
    main()
