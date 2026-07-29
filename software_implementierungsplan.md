# Software-Implementierungsplan – KI-Refactoring-Agent

**Projekt:** Entwicklung eines spezialisierten KI-Refactoring-Coding-Agents (≤ 250 Zeilen)
**Zweck:** Technische Umsetzungsanleitung für die Software-Komponente
**Version:** 1.0
**Datum:** 29.07.2026
**Basierend auf:** umsetzungs_plan.md v7.0

---

## 1. Architektur-Überblick

### 1.1 System-Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    KI-Refactoring-Agent (CLI)                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   refactoring_agent.py                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐  │  │
│  │  │ CLI Parser  │  │ Ollama API   │  │ Systemprompt       │  │  │
│  │  │ (argparse)  │◄─┤ Client      │◄─┤ Management        │  │  │
│  │  └─────────────┘  └─────────────┘  └───────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ollama-Server (localhost:11434)              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Lokales Modell: qwen2.5-coder:7b / qwen3-coder:30b        │  │
│  │ /api/generate Endpunkt                                       │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 JSON-Output (für CLI-Agents)                    │
│  {"file": "...", "language": "...", "smells": [...],         │
│   "stats": {"total_smells": N, ...}}                            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Datenfluss

```
Code-Input (Datei/stdin)
         │
         ▼
   CLI-Argument-Parsing (argparse)
         │
         ▼
   Code-Extraktion (Datei lesen oder stdin)
         │
         ▼
   Ollama-API-Request Vorbereitung
         │  ┌─────────────────────────────┐
         │  │ Systemprompt + Code + Model   │
         │  │ Temperature: 0.0-0.3          │
         │  │ Format: JSON                  │
         │  └─────────────────────────────┘
         │
         ▼
   HTTP POST an http://localhost:11434/api/generate
         │
         ▼
   KI-Response (JSON mit Refactoring-Vorschlägen)
         │
         ▼
   JSON-Output (stdout) für andere CLI-Agents
```

---

## 2. Komponenten-Spezifikation

### 2.1 Hauptkomponenten

| Komponente | Verantwortung | Zeilen-Budget | Abhängigkeiten |
|------------|---------------|---------------|----------------|
| CLI-Parser | Argument-Parsing, Unterkommandos | 30-40 | argparse |
| Datei-I/O | Code von Datei/stdin lesen | 15-20 | sys, os |
| Ollama-Client | API-Kommunikation, Error-Handling | 50-60 | requests, json |
| Systemprompt | Prompt-Management | 10-15 | (keine) |
| Output-Formatter | JSON-Formatierung, Ausgabe | 10-15 | json |
| Main-Funktion | Orchestrierung | 20-25 | alle |
| **Gesamt** | | **≤ 250** | |

### 2.2 Datei-Struktur

```
projekt/
├── src/
│   └── refactoring_agent.py      # <= 250 Zeilen (Hauptdatei)
├── prompts/
│   └── system_prompt.txt          # Externer Systemprompt (optional)
├── tests/
│   └── test_agent.py              # Unit-Tests mit Mock-Ollama
└── README.md
```

---

## 3. Implementierungs-Phasen

### Phase A: Core-Funktionalität (4-5 Stunden)

#### A.1 CLI-Grundgerüst (1 Stunde)
- [ ] argparse-Parser mit Unterkommando `analyze` implementieren
- [ ] Argument `--file` für Datei-Input
- [ ] Argument `--model` mit Default `qwen2.5-coder:7b`
- [ ] Argument `--temperature` (0.0-1.0, Default: 0.1)
- [ ] Argument `--format` (json/text, Default: json)
- [ ] stdin-Unterstützung für Piping

**Code-Skelett:**
```python
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="KI-Refactoring-Agent")
    subparsers = parser.add_subparsers(dest="command")
    
    analyze_parser = subparsers.add_parser("analyze", help="Code analysieren")
    analyze_parser.add_argument("file", nargs="?", help="Dateipfad")
    analyze_parser.add_argument("--model", default="qwen2.5-coder:7b")
    analyze_parser.add_argument("--temperature", type=float, default=0.1)
    analyze_parser.add_argument("--format", choices=["json", "text"], default="json")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        code = read_code(args.file)
        result = analyze_code(code, args.model, args.temperature)
        print(format_output(result, args.format))

if __name__ == "__main__":
    main()
```

#### A.2 Ollama-API-Client (2 Stunden)
- [ ] HTTP-Client für POST /api/generate implementieren
- [ ] Payload-Struktur: model, system, prompt, stream=False, format=json
- [ ] Systemprompt als Konstante oder aus externer Datei
- [ ] Error-Handling: ConnectionError, Timeout, HTTP-Errors
- [ ] Response-Validierung (JSON-Parsing)

**API-Client:**
```python
import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"
TIMEOUT = 30

SYSTEM_PROMPT = """
Du bist ein spezialisierter Refactoring-Agent mit der einzigen Aufgabe,
Code zu analysieren und konkrete Refactoring-Vorschläge als JSON zu generieren.
[... Prompt aus umsetzungs_plan.md ...]
"""

def call_ollama(code: str, model: str, temperature: float) -> dict:
    payload = {
        "model": model,
        "system": SYSTEM_PROMPT,
        "prompt": f"Analysiere den folgenden Code:\n\n```\n{code}\n```",
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "top_p": 0.9
        }
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
```

#### A.3 Code-I/O (0.5 Stunden)
- [ ] Funktion zum Lesen aus Datei
- [ ] Funktion zum Lesen aus stdin
- [ ] Error-Handling: FileNotFoundError, PermissionError

**Code-I/O:**
```python
def read_code(file_path: str | None) -> str:
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise RuntimeError(f"Datei nicht gefunden: {file_path}")
        except PermissionError:
            raise RuntimeError(f"Keine Leseberechtigung: {file_path}")
    else:
        return sys.stdin.read()
```

### Phase B: Integration & Optimierung (2-3 Stunden)

#### B.1 Komponenten-Integration (1 Stunde)
- [ ] Alle Komponenten in main() zusammenführen
- [ ] Zeilenzahl prüfen (≤ 250 Zeilen)
- [ ] Code-Formatierung (PEP 8)
- [ ] Docstrings hinzufügen

#### B.2 Fehlerbehandlung & Validierung (1 Stunde)
- [ ] Ollama-Server-Verfügbarkeit prüfen
- [ ] Modell-Verfügbarkeit prüfen (GET /api/tags)
- [ ] Code-Längenlimit (z. B. 10.000 Zeichen)
- [ ] Hilfreiche Fehlermeldungen

**Erweiterte Fehlerbehandlung:**
```python
def check_ollama_availability() -> bool:
    try:
        requests.get("http://localhost:11434/api/tags", timeout=5)
        return True
    except requests.exceptions.RequestException:
        return False

def check_model_available(model: str) -> bool:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in response.json().get("models", [])]
        return model in models
    except requests.exceptions.RequestException:
        return False
```

#### B.3 Output-Formatierung (0.5 Stunden)
- [ ] JSON-Validierung der KI-Antwort
- [ ] Pretty-Print für JSON-Output
- [ ] Text-Formatierung für human-readable Output

**Output-Formatter:**
```python
import json

def format_output(response: dict, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(response, indent=2, ensure_ascii=False)
    else:
        # Text-Formatierung
        result = response.get("response", "{}")
        try:
            data = json.loads(result)
            output = []
            for smell in data.get("smells", []):
                output.append(
                    f"{smell.get('type', 'unknown')}: "
                    f"Zeile {smell.get('location', {}).get('start_line', '?')}-{smell.get('location', {}).get('end_line', '?')}"
                )
                output.append(f"  {smell.get('description', '')}")
                output.append(f"  Vorschlag: {smell.get('suggestion', '')}")
            return "\n".join(output)
        except json.JSONDecodeError:
            return result
```

### Phase C: Testing & Quality Assurance (2 Stunden)

#### C.1 Unit-Tests mit Mock-Ollama (1 Stunde)
- [ ] Mock-Ollama-Client für Tests ohne Ollama-Server
- [ ] Tests für CLI-Argument-Parsing
- [ ] Tests für Code-I/O
- [ ] Tests für API-Client
- [ ] Tests für Output-Formatierung

**Test-Struktur:**
```python
import pytest
from unittest.mock import patch, MagicMock
import refactoring_agent as agent

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError("Error")

@patch('requests.post')
def test_call_ollama_success(mock_post):
    mock_post.return_value = MockResponse(
        {"response": '{"file": "test.py", "smells": []}'}, 200
    )
    result = agent.call_ollama("def foo(): pass", "qwen2.5-coder:7b", 0.1)
    assert "response" in result

@patch('requests.post')
def test_call_ollama_error(mock_post):
    mock_post.side_effect = requests.exceptions.ConnectionError("No connection")
    with pytest.raises(RuntimeError):
        agent.call_ollama("code", "model", 0.1)

def test_read_code_from_file(tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    assert agent.read_code(str(test_file)) == "def foo(): pass"

def test_read_code_from_stdin(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO("def bar(): pass"))
    assert agent.read_code(None) == "def bar(): pass"
```

#### C.2 Integrationstests (1 Stunde)
- [ ] Test mit echtem Ollama (falls verfügbar)
- [ ] Test mit verschiedenen Code-Beispielen
- [ ] Test mit verschiedenen Modellen
- [ ] Performance-Tests (< 5 Sekunden für 100 Zeilen Code)

---

## 4. Systemprompt-Optimierung

### 4.1 Prompt-Struktur

Der Systemprompt muss folgende Anforderungen erfüllen:
- **Rolle:** Spezialisierter Refactoring-Agent
- **Aufgabe:** Code analysieren und Refactoring-Vorschläge generieren
- **Ausgabeformat:** Strenges JSON-Format
- **Code Smells:** Liste der zu erkennenden Probleme
- **Regeln:** Präzision, Code-Beispiele, Begründungen

### 4.2 Prompt-Versionierung

```
prompts/
├── system_prompt_v1.md    # Erste Version
├── system_prompt_v2.md    # Optimiert nach Tests
└── system_prompt.md       # Aktuelle Version (Symlink)
```

### 4.3 Prompt-Testing

- [ ] Test mit verschiedenen Code-Beispielen
- [ ] Validierung der JSON-Ausgabe
- [ ] Überprüfung der Vorschlagsqualität
- [ ] Anpassung basierend auf Testergebnissen

---

## 5. Zeilen-Budget-Verteilung

### Aktuelle Planung (≈ 230 Zeilen)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Imports (10 Zeilen)                                       │
├─────────────────────────────────────────────────────────────┤
│ 2. Konstanten (20 Zeilen)                                    │
│    - OLLAMA_API_URL                                         │
│    - TIMEOUT                                                │
│    - SYSTEM_PROMPT (15 Zeilen)                               │
├─────────────────────────────────────────────────────────────┤
│ 3. Helper-Funktionen (40 Zeilen)                             │
│    - read_code()                                           │
│    - check_ollama_availability()                            │
│    - check_model_available()                                │
│    - format_output()                                        │
├─────────────────────────────────────────────────────────────┤
│ 4. Core-Funktionen (60 Zeilen)                              │
│    - call_ollama()                                          │
│    - analyze_code()                                         │
├─────────────────────────────────────────────────────────────┤
│ 5. CLI-Setup (40 Zeilen)                                    │
│    - ArgumentParser                                         │
│    - Subcommands                                            │
├─────────────────────────────────────────────────────────────┤
│ 6. Main-Funktion (20 Zeilen)                                │
│    - Orchestrierung                                         │
│    - Error-Handling                                         │
├─────────────────────────────────────────────────────────────┤
│ 7. Entry Point (5 Zeilen)                                   │
│    - if __name__ == "__main__"                              │
├─────────────────────────────────────────────────────────────┤
│ 8. Puffer (25 Zeilen)                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Abhängigkeiten

### 6.1 Python-Pakete

| Paket | Version | Zweck | Optional |
|-------|---------|-------|----------|
| requests | >= 2.31 | HTTP-Client für Ollama-API | Nein |
| argparse | (stdlib) | CLI-Argument-Parsing | Nein |
| json | (stdlib) | JSON-Verarbeitung | Nein |
| sys | (stdlib) | stdin/stdout | Nein |
| pytest | >= 7.0 | Testing | Ja (für Entwicklung) |
| pytest-mock | >= 3.0 | Mocking | Ja (für Entwicklung) |

### 6.2 Externe Abhängigkeiten

| Komponente | Version | Zweck |
|------------|---------|-------|
| Ollama | >= 0.3.0 | Lokale KI-Modell-Server |
| qwen2.5-coder:7b | latest | **Primäres Refactoring-Modell** |
| qwen3-coder:30b | latest | Alternative für komplexe Aufgaben |
| deepseek-coder:33b | latest | Alternative für komplexe Aufgaben |
| magicoder:7b | latest | Alternative für schnelle Analyse |

---

## 7. Build & Installation

### 7.1 Entwicklungs-Umgebung

```bash
# 1. Python-Virtual-Environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Abhängigkeiten installieren
pip install requests pytest pytest-mock

# 3. Ollama installieren (falls nicht vorhanden)
curl -fsSL https://ollama.com/install.sh | sh

# 4. Modell herunterladen
ollama pull qwen2.5-coder:7b

# 5. Agent installieren (optional, für globale Nutzung)
pip install -e .
```

### 7.2 Projekt-Struktur für pip-Installation

```
refactoring-agent/
├── pyproject.toml
├── src/
│   └── refactoring_agent/
│       ├── __init__.py
│       ├── __main__.py      # Entry Point
│       └── agent.py         # Hauptlogik
└── README.md
```

**pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "refactoring-agent"
version = "0.1.0"
description = "KI-Refactoring-Agent für Code-Analyse"
readme = "README.md"
requires-python = ">=3.10"
dependencies = ["requests>=2.31"]

[project.scripts]
refactoring-agent = "refactoring_agent.__main__:main"
```

---

## 8. Usage-Beispiele

### 8.1 Grundlegende Nutzung

```bash
# Datei analysieren
refactoring-agent analyze src/service.py

# Mit spezifischem Modell
refactoring-agent analyze src/service.py --model deepseek-coder:33b

# Mit höherer Temperatur (mehr Kreativität)
refactoring-agent analyze src/service.py --temperature 0.3

# Text-Output statt JSON
refactoring-agent analyze src/service.py --format text
```

### 8.2 Piping & Agenten-Anbindung

```bash
# Code via stdin
cat src/service.py | refactoring-agent analyze

# Mit Here-Doc
refactoring-agent analyze <<'EOF'
def process_data(x):
    if x > 0:
        return x * 2
    else:
        return x / 2
EOF

# In anderen Skripten
result=$(refactoring-agent analyze src/service.py --format json)
echo "$result" | jq '.smells | length'
```

### 8.3 Python-API (für andere Agenten)

```python
import subprocess
import json

def get_refactoring_suggestions(file_path: str, model: str = "qwen2.5-coder:7b") -> dict:
    result = subprocess.run(
        ["refactoring-agent", "analyze", file_path, "--model", model, "--format", "json"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Agent Error: {result.stderr}")
    return json.loads(result.stdout)

# Usage
suggestions = get_refactoring_suggestions("src/service.py")
for smell in suggestions["smells"]:
    print(f"{smell['type']} at line {smell['location']['start_line']}")
```

---

## 9. Qualitätskriterien

### 9.1 Code-Qualität

- [ ] **Zeilenlimit:** ≤ 250 Zeilen produktiver Code
- [ ] **PEP 8:** Code folgt Python-Style-Guide
- [ ] **Docstrings:** Alle Funktionen dokumentiert
- [ ] **Typ-Hints:** Wo sinnvoll eingesetzt
- [ ] **Error-Handling:** Alle möglichen Fehler abgedeckt

### 9.2 Test-Coverage

- [ ] **Unit-Tests:** > 90% Coverage der Core-Funktionen
- [ ] **Integrationstests:** Alle CLI-Kommandos getestet
- [ ] **Mock-Tests:** Ohne Ollama-Server ausführbar
- [ ] **Echte API-Tests:** Mit Ollama (optional)

### 9.3 Performance

- [ ] **Response-Zeit:** < 5 Sekunden für 100 Zeilen Code
- [ ] **Speicher:** < 100MB RAM (Agent selbst, ohne Modell)
- [ ] **Skalierbarkeit:** Verarbeitet Dateien bis 10.000 Zeilen

---

## 10. Risiken & Mitigationsstrategien

| Risiko | Wahrscheinlichkeit | Auswirkung | Mitigation |
|--------|-------------------|------------|------------|
| Ollama nicht verfügbar | Hoch | Hoch | Klare Fehlermeldung, Installationsanleitung |
| Modell nicht verfügbar | Mittel | Hoch | Modell-Liste prüfen, Fallback-Modell |
| JSON-Output ungültig | Mittel | Mittel | Validierung, Re-Prompting |
| Zeilenlimit überschritten | Mittel | Hoch | Regelmäßige Zeilenzählung |
| Performance-Probleme | Niedrig | Mittel | Timeout erhöhen, Modell wechseln |
| Speicher-Probleme | Niedrig | Hoch | Stream-Modus prüfen |

---

## 11. Checkliste für Abnahme

### [ ] Core-Funktionalität
- [ ] CLI-Tool funktioniert mit `analyze`-Kommando
- [ ] Datei-Input funktioniert
- [ ] stdin-Input funktioniert
- [ ] Ollama-API-Anbindung funktioniert
- [ ] JSON-Output ist valide
- [ ] Text-Output ist lesbar

### [ ] Fehlerbehandlung
- [ ] Datei nicht gefunden → hilfreiche Fehlermeldung
- [ ] Ollama nicht erreichbar → hilfreiche Fehlermeldung
- [ ] Modell nicht verfügbar → hilfreiche Fehlermeldung
- [ ] Ungültige API-Antwort → Graceful Degradation

### [ ] Qualitätschecks
- [ ] ≤ 250 Zeilen Code
- [ ] PEP 8 konform
- [ ] Alle Funktionen dokumentiert
- [ ] Unit-Tests laufen erfolgreich
- [ ] Integrationstests laufen erfolgreich

### [ ] Dokumentation
- [ ] README.md mit Installations- und Nutzungsanleitung
- [ ] Systemprompt dokumentiert
- [ ] API-Spezifikation dokumentiert
- [ ] Beispiele enthalten

---

## 12. Nächste Schritte

1. **Implementierung starten** mit CLI-Grundgerüst
2. **Ollama-API-Client** implementieren
3. **Systemprompt finalisieren** und testen
4. **Integration** aller Komponenten
5. **Tests schreiben** und ausführen
6. **Zeilenzahl prüfen** und optimieren
7. **Dokumentation** vervollständigen
8. **Abnahmetests** durchführen

---

## Anhang: Quick-Start für Entwickler

```bash
# 1. Repository klonen
git clone <repository-url>
cd refactoring-agent

# 2. Virtuelle Umgebung einrichten
python -m venv venv
source venv/bin/activate

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. Ollama vorbereiten
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:7b
ollama serve

# 5. Agent testen
python -m refactoring_agent analyze examples/sample.py

# 6. Tests ausführen
pytest tests/
```

**requirements.txt:**
```
requests>=2.31
pytest>=7.0
pytest-mock>=3.0
```
