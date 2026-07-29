#!/usr/bin/env python3
"""KI-Refactoring-Agent - CLI-Tool für Code-Analyse via Ollama-API."""

import argparse
import sys
import json
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
TIMEOUT = 120

SYSTEM_PROMPT = """Du bist ein spezialisierter Refactoring-Agent mit der einzigen Aufgabe,
Code zu analysieren und konkrete Refactoring-Vorschläge als JSON zu generieren.
Erkenne: Duplikate, lange Methoden (>20 Zeilen), unklare Namen, gemischte Verantwortlichkeiten,
hohes zyklomatische Komplexität, unnötige Kommentare, Magic Numbers/Strings, zu viele Parameter (>4).
Ausgabeformat: {"file":"...","language":"...","smells":[{"type":"...","location":{"file":"...","start_line":N,"end_line":N},
"description":"...","severity":"high|medium|low","suggestion":"...","reason":"...","impact":"readability|maintainability|testability|performance"}],
"stats":{"total_smells":N,"high":N,"medium":N,"low":N,"coverage":"X%"}}
Regeln: Sei präzise, gib Code-Beispiele, erkläre Begründungen, ändere kein Verhalten."""


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


def apply_refactoring(code, smells, output_file):
    """Wendet den ersten Refactoring-Vorschlag an und schreibt in output_file."""
    if not smells:
        raise RuntimeError("Keine Refactoring-Vorschläge gefunden")
    
    smell = smells[0]
    lines = code.split('\n')
    start_line = smell.get('location', {}).get('start_line', 1) - 1
    end_line = smell.get('location', {}).get('end_line', 1) - 1
    
    suggestion = smell.get('suggestion', '')
    
    if start_line >= 0 and end_line < len(lines):
        lines[start_line] = f"# REFACCTORING VORSCHLAG: {smell.get('description', '')}\n# {smell.get('reason', '')}\n# {suggestion}\n" + lines[start_line]
        refactored_code = '\n'.join(lines)
    else:
        refactored_code = code + f"\n\n# REFACCTORING VORSCHLÄGE:\n"
        for s in smells:
            refactored_code += f"# {s.get('type', 'unknown')}: {s.get('description', '')}\n"
            refactored_code += f"# Vorschlag: {s.get('suggestion', '')}\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(refactored_code)
    
    return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="KI-Refactoring-Agent für Code-Analyse und Refactoring"
    )
    subparsers = parser.add_subparsers(dest="command")
    
    # Analyze-Kommando
    analyze_parser = subparsers.add_parser("analyze", help="Code analysieren")
    analyze_parser.add_argument("file", nargs="?", help="Dateipfad (optional)")
    analyze_parser.add_argument(
        "--model", default="qwen2.5-coder:7b",
        choices=["qwen2.5-coder:7b", "qwen3-coder:30b", "qwen3-coder:7b", 
                 "deepseek-coder:33b", "deepseek-coder:6.7b", 
                 "devstral:24b", "magicoder:7b"],
        help="Ollama-Modell (default: qwen2.5-coder:7b)"
    )
    analyze_parser.add_argument(
        "--temperature", type=float, default=0.1, help="Kreativität (0.0-1.0)"
    )
    analyze_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Ausgabeformat"
    )
    
    # Apply-Kommando
    apply_parser = subparsers.add_parser(
        "apply", help="Refactoring-Vorschläge anwenden und in Datei schreiben"
    )
    apply_parser.add_argument("file", help="Dateipfad der zu refactorenden Datei")
    apply_parser.add_argument(
        "--output", "-o", required=True, help="Zieldatei für den refaktorierten Code"
    )
    apply_parser.add_argument(
        "--model", default="qwen2.5-coder:7b",
        choices=["qwen2.5-coder:7b", "qwen3-coder:30b", "qwen3-coder:7b", 
                 "deepseek-coder:33b", "deepseek-coder:6.7b", 
                 "devstral:24b", "magicoder:7b"],
        help="Ollama-Modell (default: qwen2.5-coder:7b)"
    )
    apply_parser.add_argument(
        "--temperature", type=float, default=0.1, help="Kreativität (0.0-1.0)"
    )
    
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "analyze":
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

        print(format_output(result, args.format))
    
    elif args.command == "apply":
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
            print("Keine Refactoring-Vorschläge gefunden.", file=sys.stderr)
            sys.exit(1)

        try:
            output_file = apply_refactoring(code, smells, args.output)
            print(f"Refactoring angewendet. Ergebnis geschrieben nach: {output_file}")
            print(f"Anzahl der Vorschläge: {len(smells)}")
            for i, smell in enumerate(smells, 1):
                loc = smell.get("location", {})
                print(f"  {i}. {smell.get('type', 'unknown')}: Zeile {loc.get('start_line', '?')}-{loc.get('end_line', '?')}")
        except RuntimeError as e:
            print(f"Fehler beim Anwenden: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
