# Umsetzungsplan – KI-Refactoring-Agent

**Projekt:** Entwicklung eines spezialisierten KI-Refactoring-Agents (≤ 250 Zeilen) zur Generierung von Refactoring-Vorschlägen. Der Agent kommuniziert per Ollama-API mit lokalen Modellen und hat die einzige Aufgabe des Refactorings.  
**Auftraggeber:** CampusCode Software GmbH  
**Auftragnehmer:** Projektgruppe KI-Anwendungsentwicklung  
**Version:** 7.0  
**Datum:** 29.07.2026

---

## 1. Übersicht

| **Aspekt** | **Details** |
|------------|-------------|
| **Ziel** | Entwicklung eines **spezialisierten KI-Refactoring-Agents** (Komponente mit ≤ 250 Zeilen produktivem Code). Der Agent kommuniziert per **Ollama-API** mit lokalen Modellen und hat **ausschließlich die Aufgabe des Refactorings**. Nachweis durch Tests, Linting, Review und Qualitätskennzahlen. |
| **Zeitrahmen** | 16 Unterrichtsstunden (à 45 Minuten) |
| **Budget** | 1.000 € (fiktiv) |
| **Sprache/Stack** | Python + requests, argparse, Ollama-API (lokale Modelle: qwen3-coder, deepseek-coder), Unit-Test-Framework, Linter, Git |
| **Rahmenbedingungen** | Komponente (KI-Refactoring-Agent) mit höchstens 250 Zeilen produktivem Code. Keine Veränderung öffentlicher Schnittstellen ohne Freigabe. **Keine Secrets an nicht freigegebene Dienste** (nur lokale Ollama-API). Jeder Schritt muss rückgängig machbar sein. Tests müssen vor und nach der Änderung erfolgreich laufen. Menschliches Code Review ist verpflichtend. |

---

## 2. Projektziel

Ziel ist eine besser strukturierte, wartbare Komponente (der **KI-Refactoring-Agent**) mit prüfbarem Qualitätsnachweis. Der Agent:

- **Hat ausschließlich die Aufgabe des Refactorings** (keine anderen Aufgaben)
- **Kommuniziert per Ollama-API** (`http://localhost:11434/api/generate`) mit **lokalen Ollama-Modellen**
- **Nutzt einen Systemprompt**, der seine Rolle als Refactoring-Experte definiert
- **Ist als CLI-Tool nutzbar** (z. B. `refactoring-agent analyze code.py`)
- **Generiert umsetzbare Refactoring-Vorschläge** (Code Smells erkennen, Lösungen vorschlagen)
- **Ist für die Anbindung an andere CLI-Agents ausgelegt** (stdin/stdout, JSON-Output)
- **Ist nachvollziehbar dokumentiert** (Prompts, Entscheidungen, Änderungen)

Der KI-Refactoring-Agent ist das **Hauptprodukt** des Projekts und agiert als **spezialisierter Coding-Agent mit definierter Rolle und Aufgabe**. Die eigentliche Intelligenz kommt von den lokalen Ollama-Modellen.

---

## 3. Phasen und Meilensteine

### Phase 0: Vorbereitung (1 Stunde)
**Ziel:** Projektumfeld klären und Anforderungen an den Refactoring-Agenten definieren.

| **Aufgabe** | **Verantwortlich** | **Zeit** | **Ergebnis** |
|-------------|---------------------|----------|---------------|
| Projektauftrag analysieren | Team | 0,25 h | Checkliste der Anforderungen |
| Ollama-Installation und Modellauswahl prüfen | Team | 0,5 h | Entscheidung: Welches lokale Modell? (z. B. qwen3-coder:30b, deepseek-coder:33b) |
| Systemprompt für Refactoring-Agent entwerfen | Team | 0,25 h | Erste Version des Systemprompts |
| Git-Repository anlegen und initialisieren | Team | 0,25 h | Lokales Repository mit main-Branch |

**Meilenstein 0:** Ollama-Umgebung geklärt, Systemprompt-Grundgerüst erstellt, Repository bereit.

---

### Phase 1: Analysephase (3 Stunden)
**Ziel:** Anforderungen an den Refactoring-Agenten detaillieren und technische Machbarkeit prüfen.

| **Aufgabe** | **Verantwortlich** | **Zeit** | **Ergebnis** |
|-------------|---------------------|----------|---------------|
| Beschreibung des Agenten-Verhaltens und relevanter Risiken | Team | 0,5 h | Dokumentation: Referenzverhalten und Risikoanalyse |
| Code Smells für Refactoring definieren | Team | 0,5 h | Liste: Duplikate, lange Methoden, unklare Namen, etc. |
| Ollama-API-Spezifikation prüfen | Team | 0,5 h | Dokumentation: /api/generate Endpunkt |
| Systemprompt finalisieren | Team | 0,5 h | Optimierter Prompt für Refactoring-Aufgabe |
| Beispiel-Inputs und Expected Outputs erstellen | Team | 0,5 h | Testfälle für den Agenten |
| CLI-Output-Format festlegen | Team | 0,5 h | Entscheidung: JSON (für Agenten) |

**Dokumente:**
- `dokumentation/analyse/anforderungen.md`
- `dokumentation/analyse/ollama_api.md` (API-Spezifikation)
- `dokumentation/analyse/testfaelle.md`
- `dokumentation/analyse/verhalten_und_risiken.md`
- `prompts/system_prompt_v1.md` (erste Version)

**Meilenstein 1:** Anforderungen und Machbarkeit dokumentiert, Systemprompt finalisiert, Testfälle vorbereitet.

---

### Phase 2: Designphase (2 Stunden)
**Ziel:** Architektur und Implementierungsplan für den Refactoring-Agenten erstellen.

| **Aufgabe** | **Verantwortlich** | **Zeit** | **Ergebnis** |
|-------------|---------------------|----------|---------------|
| CLI-Architektur entwerfen | Team | 0,5 h | Diagramm: Komponenten, Datenfluss |
| Systemprompt optimieren | Team | 1 h | Finaler Prompt mit Rolle, Aufgabe, Ausgabeformat |
| Reviewkriterien für KI-Ausgaben definieren | Team | 0,5 h | Checkliste: Wann ist ein Vorschlag gültig? |

**Dokumente:**
- `dokumentation/design/architektur.md`
- `prompts/system_prompt.md` (finaler Systemprompt)
- `prompts/review_kriterien.md`

**Meilenstein 2:** Design finalisiert, Systemprompt optimiert, Implementierung geplant (Code-Umfang ≤ 250 Zeilen sichergestellt).

---

### Phase 3: Implementierungsphase (6 Stunden)
**Ziel:** Schrittweise Entwicklung des KI-Refactoring-Agents (≤ 250 Zeilen) mit Ollama-API-Anbindung.

| **Aufgabe** | **Verantwortlich** | **Zeit** | **Ergebnis** |
|-------------|---------------------|----------|---------------|
| CLI-Gerüst mit argparse implementieren | Team | 0,5 h | Basis-Tool mit Unterkommando `analyze` |
| Ollama-API-Anbindung implementieren | Team | 1,5 h | HTTP-Requests an localhost:11434/api/generate |
| Systemprompt integrieren | Team | 0,5 h | Prompt als Konstante im Code |
| Code-Eingabe verarbeiten (Datei/stdin) | Team | 0,5 h | Lesen von Dateien oder stdin |
| Ollama-Antwort parsen | Team | 1 h | Extraktion der Vorschläge aus KI-Ausgabe |
| CLI-Ausgabe formatieren (JSON) | Team | 0,5 h | Strukturierte JSON-Ausgabe für Agenten |
| Fehlerbehandlung implementieren | Team | 0,5 h | Handling von API-Errors, Timeouts |
| Zeilenanzahl prüfen (≤ 250 Zeilen) | Team | 0,25 h | Bestätigung der Code-Länge |
| Änderungen schrittweise umsetzen und versionieren | Team | 0,25 h | Kleine Commits mit klaren Messages |

**Dokumente:**
- `src/refactoring_agent.py` (der Agent, ≤ 250 Zeilen)

**Meilenstein 3:** Refactoring-Agent implementiert, Ollama-Anbindung funktionsfähig, CLI nutzbar, Code-Länge ≤ 250 Zeilen, Änderungen versioniert.

---

### Phase 4: Testphase (2 Stunden)
**Ziel:** Qualitätssicherung des Refactoring-Agents.

| **Aufgabe** | **Verantwortlich** | **Zeit** | **Ergebnis** |
|-------------|---------------------|----------|---------------|
| Vorher-Tests erstellen oder ergänzen | Team | 0,5 h | Automatisierte Charakterisierungs- und Unit-Tests |
| Unit-Tests für den Agenten erstellen | Team | 0,5 h | Tests der CLI-Logik (mit Mock-Ollama) |
| CLI-Integrationstests durchführen | Team | 0,25 h | Validierung der Command-Line-Schnittstelle |
| Ollama-API-Tests durchführen | Team | 0,25 h | Tests mit echtem lokalem Ollama |
| Systemprompt-Tests durchführen | Team | 0,25 h | Validierung mit verschiedenen Code-Beispielen |
| Testfälle aus Phase 1 ausführen | Team | 0,25 h | Validierung mit Beispiel-Inputs/Outputs |

**Dokumente:**
- `tests/charakterisierung_test.py`
- `tests/unit_test.py` (mit Mock-Ollama)
- `tests/cli_integration_test.py`
- `tests/ollama_api_test.py`
- `dokumentation/tests/testprotokoll.md`

**Meilenstein 4:** Refactoring-Agent getestet, Ollama-Anbindung verifiziert, alle Checks bestanden.

---

### Phase 5: Abschlussphase (2 Stunden)
**Ziel:** Dokumentation finalisieren und Lessons Learned aufbereiten.

| **Aufgabe** | **Verantwortlich** | **Zeit** | **Ergebnis** |
|-------------|---------------------|----------|---------------|
| Qualitätskennzahlen vergleichen | Team | 0,25 h | Vergleich von Vorschlagsqualität, Abdeckungsrate |
| Übernommene und verworfene KI-Vorschläge begründen | Team | 0,5 h | `dokumentation/entscheidungen.md` |
| Lessons Learned und nächste Schritte präsentieren | Team | 0,5 h | `dokumentation/lessons_learned.md` |
| Kurzbericht erstellen | Team | 0,25 h | `abschlussbericht.md` |
| Code-Dokumentation erstellen | Team | 0,25 h | Code-Kommentare und/oder Docstring |
| Benutzerdokumentation erstellen | Team | 0,25 h | `README.md` mit Installations- und Nutzungsanleitung |

**Dokumente:**
- `README.md` (mit Ollama-Installation und CLI-Befehlen)
- `dokumentation/abschluss/qualitaetsvergleich.md`
- `dokumentation/abschluss/entscheidungen.md`
- `dokumentation/abschluss/lessons_learned.md`
- `abschlussbericht.md`

**Meilenstein 5:** Projekt abgeschlossen, alle Dokumente vorbereitet.

---

## 4. Zeitplan (Gesamt: 16 Stunden)

| **Phase** | **Dauer** | **Start** | **Ende** | **Verantwortlich** |
|-----------|-----------|-----------|----------|--------------------|
| Vorbereitung | 1 h | Stunde 1 | Stunde 1 | Team |
| Analysephase | 3 h | Stunde 2-4 | Stunde 4 | Team |
| Designphase | 2 h | Stunde 5-6 | Stunde 6 | Team |
| Implementierungsphase | 6 h | Stunde 7-12 | Stunde 12 | Team |
| Testphase | 2 h | Stunde 13-14 | Stunde 14 | Team |
| Abschlussphase | 2 h | Stunde 15-16 | Stunde 16 | Team |

---

## 5. Verantwortlichkeiten und Rollen

| **Rolle** | **Aufgaben** | **Besetzung** |
|-----------|--------------|---------------|
| Projektleiter | Koordination, Zeitmanagement, finale Abnahme | [Name] |
| Prompt-Engineer | Systemprompt-Optimierung, KI-Fine-Tuning | [Name] |
| API-Entwickler | Ollama-API-Anbindung, HTTP-Requests | [Name] |
| CLI-Entwickler | CLI-Implementierung, Argument-Parsing | [Name] |

*Hinweis: Bei kleinem Team (2-3 Personen) können Rollen doppelt besetzt werden.*

---

## 6. Qualitätskriterien und Nicht-Ziele

### Qualitätskriterien (MUSS)
- [ ] Der KI-Refactoring-Agent hat maximal 250 Zeilen produktiven Code (ohne Tests, ohne Kommentare).
- [ ] Der Agent hat **ausschließlich die Aufgabe des Refactorings**.
- [ ] Der Agent kommuniziert per **Ollama-API** mit lokalen Modellen.
- [ ] Der Agent nutzt einen **Systemprompt**, der seine Rolle als Refactoring-Experte definiert.
- [ ] Der Agent ist als CLI-Tool nutzbar (z. B. `refactoring-agent analyze code.py`).
- [ ] Der Agent generiert umsetzbare Refactoring-Vorschläge (konkret, nachvollziehbar).
- [ ] Der Agent ist für die Anbindung an andere CLI-Agents ausgelegt (JSON-Output).
- [ ] Alle Tests laufen erfolgreich (Unit-Tests, CLI-Tests, API-Tests).
- [ ] Der Code ist lesbar, dokumentiert und linting-konform.
- [ ] Code Review wurde durchgeführt.
- [ ] Alle Entscheidungen (Systemprompt, API-Anbindung) sind dokumentiert.
- [ ] Schrittweise Umsetzung mit kleinen Commits.
- [ ] Versionierter Systemprompt für Refactoring-Aufgabe.

### Nicht-Ziele (DARF NICHT)
- [ ] Der Agent hat andere Aufgaben als Refactoring.
- [ ] Der Agent nutzt externe APIs ohne Freigabe (nur Ollama-API mit **lokalen Modellen**).
- [ ] Der Code überschreitet 250 Zeilen produktiven Code.
- [ ] Der Agent wird produktiv eingesetzt.
- [ ] Veränderung öffentlicher Schnittstellen ohne begründete Freigabe.
- [ ] Secrets oder vertrauliche Quelltexte an nicht freigegebene Dienste senden.

---

## 7. Werkzeuge und Technologien

| **Kategorie** | **Werkzeug** | **Zweck** |
|---------------|--------------|-----------|
| Versionierung | Git + GitHub/GitLab | Code-Versionierung, Branching, Pull Requests |
| Programmiersprache | Python | Implementierung des Refactoring-Agents |
| CLI-Bibliothek | argparse (Python) | Command-Line-Interface |
| HTTP-Client | requests (Python) | Ollama-API-Anbindung |
| Test-Framework | pytest (Python) | Unit-Tests für den Agenten |
| Linting | pylint, flake8 (Python) | Code-Qualität prüfen |
| **Lokale KI** | **Ollama + lokale Modelle** (qwen3-coder:30b, deepseek-coder:33b, devstral:24b, magicoder:7b) | Refactoring-Analyse durch KI |

---

## 8. Technische Empfehlungen

### A. Systemprompt (Kern des Agents!)
```
Du bist ein **spezialisierter Refactoring-Agent** mit der **einzigen Aufgabe**, 
Code zu analysieren und konkrete Refactoring-Vorschläge zu generieren.

### Deine Rolle:
- Du bist ein **Experte für sauberen, wartbaren Code**
- Deine **einzige Aufgabe** ist das **Refactoring von Code**
- Du analysierst Code auf **Code Smells** und schlägt **konkrete Verbesserungen** vor

### Code Smells, die du erkennen sollst:
1. **Duplikate** (identischer oder ähnlicher Code in verschiedenen Stellen)
2. **Lange Methoden/Funktionen** (meist > 20 Zeilen)
3. **Unklare Variablen-/Methodennamen** (z. B. x, y, temp, doStuff())
4. **Gemischte Verantwortlichkeiten** (Single Responsibility Principle verletzt)
5. **Hohe zyklomatische Komplexität** (zu viele verschachtelte if/else)
6. **Unnötige Kommentare** (Code sollte selbsterklärend sein)
7. **Magic Numbers/Strings** (unbenannte Konstanten)
8. **Zu viele Parameter** (meist > 4 Parameter pro Funktion)

### Ausgabeformat (JSON, STRIKT einhalten!):
{
  "file": "[Dateiname]",
  "language": "[Programmiersprache]",
  "smells": [
    {
      "type": "[long_method|duplicate|unclear_name|mixed_responsibilities|high_complexity|unnecessary_comments|magic_values|too_many_parameters]",
      "location": {
        "file": "[Dateiname]",
        "start_line": [Zeile],
        "end_line": [Zeile]
      },
      "description": "[Kurze Beschreibung des Problems]",
      "severity": "high|medium|low",
      "suggestion": "[Konkreter Refactoring-Vorschlag mit Code-Beispiel]",
      "reason": "[Begründung, warum dieser Vorschlag die Code-Qualität verbessert]",
      "impact": "[Auswirkung: readability|maintainability|testability|performance]"
    }
  ],
  "stats": {
    "total_smells": [Anzahl],
    "high": [Anzahl],
    "medium": [Anzahl],
    "low": [Anzahl],
    "coverage": "[Prozent der analysierten Code-Zeilen]"
  }
}

### Wichtige Regeln:
1. **Sei präzise und konkret** in deinen Vorschlägen
2. **Gib immer Code-Beispiele** für die vorgeschlagenen Änderungen
3. **Erkläre immer die Begründung** für jeden Vorschlag
4. **Berücksichtige die Programmiersprache** des Codes
5. **Generiere NUR Refactoring-Vorschläge**, keine neuen Features
6. **Achte darauf, dass das Verhalten des Codes unverändert bleibt**
7. **Nutze das exakte JSON-Format** ohne Abweichungen
```

### B. Ollama-API-Anbindung
```python
import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = """[Hier der Systemprompt aus A]"""

def call_ollama(code: str, model: str = "qwen3-coder:30b", temperature: float = 0.1) -> str:
    """
    Sendet Anfrage an Ollama-API mit Systemprompt und Code.
    
    Args:
        code: Der zu analysierende Code
        model: Ollama-Modellname (z. B. 'qwen3-coder:30b', 'deepseek-coder:33b')
        temperature: Kreativität (0.0-1.0, niedrig für deterministischere Ergebnisse)
    
    Returns:
        Die KI-Antwort als String
    """
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
            timeout=30
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama API Error: {e}") from e
```

### C. CLI-Struktur (argparse)
```python
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description="KI-Refactoring-Agent für Code-Analyse (nutzt Ollama mit lokalen Modellen)"
    )
    parser.add_argument(
        "file", 
        nargs="?", 
        help="Dateipfad des zu analysierenden Codes (optional, sonst stdin)"
    )
    parser.add_argument(
        "--model", 
        default="qwen3-coder:30b",
        choices=["qwen3-coder:30b", "qwen3-coder:7b", "deepseek-coder:33b", "deepseek-coder:6.7b", "devstral:24b", "magicoder:7b"],
        help="Ollama-Modell (default: qwen3-coder:30b)"
    )
    parser.add_argument(
        "--temperature", 
        type=float, 
        default=0.1,
        help="Kreativität der KI (0.0-1.0, default: 0.1)"
    )
    
    args = parser.parse_args()
    
    # Code einlesen (Datei oder stdin)
    if args.file:
        with open(args.file, "r") as f:
            code = f.read()
    else:
        code = sys.stdin.read()
    
    # KI aufrufen
    result = call_ollama(code, args.model, args.temperature)
    
    # Ausgabe
    print(result)

if __name__ == "__main__":
    main()
```

### D. Empfohlene Ollama-Modelle für Refactoring

| **Modell** | **Größe** | **Eignung** | **Empfehlung** | **Hardware** |
|------------|-----------|-------------|----------------|--------------|
| `qwen3-coder:30b` | ~19GB (Q4_K_M) | ✅✅✅✅✅ **Beste Qualität/GB** | **Beste Wahl für Refactoring** | 24GB RAM / 19GB VRAM |
| `deepseek-coder:33b` | ~24GB | ✅✅✅✅✅ **95% Code-Korrektheit** | Top für komplexe Aufgaben | 32GB RAM / 24GB VRAM |
| `devstral:24b` | ~14GB | ✅✅✅✅✅ **Agentic Coding** | 46.8% SWE-Bench Verified | 16GB VRAM |
| `qwen3-coder:7b` | ~4GB | ✅✅✅✅ **Schnell & effizient** | Gut für CPU-only Setups | 8GB RAM |
| `magicoder:7b` | ~4GB | ✅✅✅✅ **60+ Tokens/Sek.** | Schnellste Alternative | 8GB RAM |
| `gemma4:26b-a4b` | ~16GB | ✅✅✅✅ **Mixture of Experts** | Vielseitig für Coding | 16GB VRAM |

---

## 9. Ollama-Installation und Nutzung

### Vorraussetzungen
1. **Ollama installiert** (https://ollama.com)
2. **Modell heruntergeladen** (z. B. `ollama pull qwen3-coder:30b`)
3. **Ollama-Server läuft** (standardmäßig auf `http://localhost:11434`)

### Installationsanleitung (für README.md)
```bash
# 1. Ollama installieren
curl -fsSL https://ollama.com/install.sh | sh

# 2. Refactoring-Modell herunterladen (empfohlen: qwen3-coder:30b oder deepseek-coder:33b)
ollama pull qwen3-coder:30b

# 3. Ollama-Server starten (falls nicht automatisch)
ollama serve

# 4. Agenten testen
refactoring-agent analyze src/service.py

# 5. Alternative Modelle ausprobieren
refactoring-agent analyze src/service.py --model deepseek-coder:33b
refactoring-agent analyze src/service.py --model magicoder:7b
```

### Ollama-API-Endpunkte
- **Generieren:** `POST /api/generate` – Hauptendpunkt für Code-Analyse
- **Modellliste:** `GET /api/tags` – Liste verfügbarer Modelle
- **Modellinfo:** `GET /api/show/{model}` – Details zu einem Modell

---

## 10. Agenten-Anbindung

### Anbindung an CLI-Agents
Der Refactoring-Agent ist **speziell für die Nutzung durch andere CLI-Agents** ausgelegt.

#### 1. Direkter Aufruf per `subprocess`
```python
import subprocess
import json

# Agent ruft den Refactoring-Agent auf
result = subprocess.run(
    ["refactoring-agent", "analyze", "code.py"],
    capture_output=True,
    text=True
)

# Agent verarbeitet das JSON-Ergebnis
suggestions = json.loads(result.stdout)
for smell in suggestions["smells"]:
    print(f"{smell['type']} in {smell['location']['file']}:{smell['location']['start_line']}")
    print(f"  Vorschlag: {smell['suggestion']}")
```

#### 2. stdin-Piping (für Streaming/Integration)
```bash
# Agent pipes Code an den Refactoring-Agent
cat code.py | refactoring-agent analyze

# Oder mit Here-Doc
refactoring-agent analyze <<'EOF'
def process_data(x):
    if x > 0:
        return x * 2
    else:
        return x / 2
EOF
```

#### 3. Integration in Agenten-Frameworks

| **Framework** | **Anbindungsmethode** | **Beispiel** |
|---------------|----------------------|-------------|
| Mistral Vibe | Tool-Call | Als externes Tool registrieren |
| CrewAI | Custom Tool | Als `RefactoringTool` einbinden |
| LangChain | Function Calling | Als Python-Funktion mit API-Aufruf |
| Autogen | Tool Use | Als Tool für den Agenten |
| Shell-Skripte | subprocess | `$(refactoring-agent analyze code.py)` |

---

## 11. Risikomanagement

| **Risiko** | **Eintrittswahrscheinlichkeit** | **Auswirkung** | **Maßnahme** |
|------------|-------------------------------|----------------|--------------|
| Refactoring-Agent überschreitet 250 Zeilen | Mittel | Hoch | Regelmäßige Zeilenzählung; Fokus auf Systemprompt und API-Wrapper |
| Ollama nicht installiert/erreichbar | Mittel | Hoch | Klare Installationsanleitung; Fehlerbehandlung im Code mit hilfreicher Fehlermeldung |
| Modell generiert unbrauchbare Vorschläge | Hoch | Mittel | Systemprompt iterativ verbessern; Review-Kriterien anwenden; Temperatur reduzieren |
| Ollama-API ändert sich | Niedrig | Mittel | API-Version prüfen; Fallback-Implementierung für ältere Versionen |
| Zeitmangel für Implementierung | Mittel | Hoch | Priorisierung der Kernfunktionen; MVP-Ansatz (nur analyze-Kommando) |
| Modell zu groß für Hardware | Niedrig | Hoch | Empfehlung für leichtere Modelle (qwen3-coder:7b, magicoder:7b) |

---

## 12. Dokumentationsstruktur

```
projekt/
├── src/                          # Refactoring-Agent-Code
│   └── refactoring_agent.py      # <= 250 Zeilen (CLI + Ollama-API + Systemprompt)
├── prompts/                      # Prompt-Vorlagen
│   └── system_prompt.md          # Systemprompt für den Agenten (versioniert!)
├── tests/                        # Tests für den Agenten
│   ├── charakterisierung_test.py
│   ├── unit_test.py              # Tests der CLI-Logik (mit Mock-Ollama)
│   ├── cli_integration_test.py
│   └── ollama_api_test.py        # Tests mit echtem Ollama (falls verfügbar)
├── dokumentation/                # Projekt-Dokumentation
│   ├── analyse/
│   │   ├── anforderungen.md
│   │   ├── ollama_api.md         # Ollama-API-Spezifikation
│   │   ├── testfaelle.md
│   │   └── verhalten_und_risiken.md
│   ├── design/
│   │   └── architekur.md
│   ├── plan/
│   │   └── metriken.md
│   ├── abschluss/
│   │   ├── qualitaetsvergleich.md
│   │   ├── entscheidungen.md
│   │   └── lessons_learned.md
│   └── README.md                 # Benutzerdokumentation
├── abschlussbericht.md           # Zusammenfassung
├── umsetzungs_plan.md            # Dieser Plan
└── README.md
```

---

## 13. Abnahmekriterien

Das Projekt gilt als erfolgreich abgeschlossen, wenn:

### 1. Refactoring-Agent
- [ ] Der Agent liegt als ausführbares CLI-Tool (**<= 250 Zeilen**) im Repository vor.
- [ ] Der Agent hat **ausschließlich die Aufgabe des Refactorings** (keine anderen Aufgaben).
- [ ] Der Agent kommuniziert per **Ollama-API** mit **lokalen Modellen**.
- [ ] Der Agent nutzt einen **Systemprompt**, der seine Rolle als Refactoring-Experte definiert.
- [ ] Der Agent ist per Command-Line nutzbar (z. B. `refactoring-agent analyze code.py`).
- [ ] Der Agent generiert **umsetzbare Refactoring-Vorschläge** (konkret, nachvollziehbar).
- [ ] Der Agent ist für die **Anbindung an andere CLI-Agents** ausgelegt (JSON-Output).
- [ ] Dokumentiertes Referenzverhalten des Agents.

### 2. Tests
- [ ] Unit-Tests decken die CLI-Logik und API-Anbindung ab (mit Mock-Ollama).
- [ ] CLI-Integrationstests laufen erfolgreich.
- [ ] Ollama-API-Tests mit echtem lokalem Ollama funktionieren.
- [ ] Systemprompt-Tests validieren die Vorschlagsqualität.
- [ ] Alle Beispiel-Testfälle aus Phase 1 laufen erfolgreich.
- [ ] Tests müssen vor und nach der Änderung erfolgreich laufen.

### 3. Qualität
- [ ] Der Code besteht Linting-Checks ohne Fehler.
- [ ] Der Code ist lesbar und dokumentiert (Kommentare/Docstrings).
- [ ] Nachweis durch Tests, Linting, Review und Qualitätskennzahlen.

### 4. Dokumentation
- [ ] Alle Anforderungen, Design-Entscheidungen und Testergebnisse sind dokumentiert.
- [ ] `README.md` enthält eine **komplette Installationsanleitung für Ollama**.
- [ ] `README.md` erklärt die **Nutzung des Agents** (CLI-Befehle, Modellauswahl).
- [ ] `abschlussbericht.md` fasst Ergebnisse, Grenzen und Lessons Learned zusammen.
- [ ] Dokumentation übernommener und verworfener KI-Vorschläge.
- [ ] Beschreibung des Refactoring-Agents und seiner Funktionsweise.
- [ ] Der **Systemprompt ist versioniert** und dokumentiert.

### 5. Prozess
- [ ] Der Code wurde versioniert (Git).
- [ ] Code Review wurde durchgeführt.
- [ ] Schrittweise Umsetzung mit kleinen Commits.
- [ ] Versionierter Systemprompt für Refactoring-Aufgabe.

---

## 14. Anhang: Vorlagen

### Commit-Nachricht (Beispiel)
```
feat: Implementiere Ollama-API-Anbindung mit Systemprompt

- Integriere Ollama-API (localhost:11434/api/generate)
- Füge Systemprompt für Refactoring-Agent hinzu
- Implementiere JSON-Output-Format
- Unterstütze qwen3-coder:30b, deepseek-coder:33b, magicoder:7b
- Zeilenanzahl: +95 (Gesamt: 180/250)

Model: qwen3-coder:30b
Review: @Teammember
```

### Testprotokoll-Vorlage
```markdown
# Testprotokoll: [Datum]

| **Testfall** | **Erwartetes Ergebnis** | **Tatsächliches Ergebnis** | **Status** |
|--------------|------------------------|----------------------------|------------|
| CLI analyze-Kommando funktioniert | JSON-Ausgabe für Testfile.py | Smells korrekt erkannt | Erfuellt |
| Ollama-API-Anbindung funktioniert | Antwort von localhost:11434 | API-Call erfolgreich | Erfuellt |
| stdin-Piping funktioniert | Code via stdin verarbeitet | Ausgabe generiert | Erfuellt |
| Systemprompt generiert valides JSON | JSON-Struktur korrekt | JSON parsbar und validiert | Erfuellt |
| Lange Methode erkannt | Methode A (25 Zeilen) erkannt | KI erkennt Methode und schlägt Extraktion vor | Erfuellt |
| Duplikaterkennung funktioniert | Duplikat in Testfile erkannt | KI erkennt Duplikat und schlägt DRY vor | Erfuellt |

## Ausgeführte Tests:
- [x] Unit-Tests (pytest, mit Mock-Ollama)
- [x] CLI-Integrationstests
- [x] Ollama-API-Tests (mit qwen3-coder:30b)
- [x] Systemprompt-Tests
- [x] Beispiel-Testfälle
- [x] Linting (pylint)

## Anmerkungen:
- Alle Kernfunktionen arbeiten wie erwartet.
- Ollama-API-Anbindung erfolgreich getestet (qwen3-coder:30b).
- Systemprompt generiert strukturierte JSON-Ausgabe nach Spezifikation.
- Performance: Analyse von 100 Zeilen Code in < 3 Sekunden (inkl. API-Aufruf).
- Modell: qwen3-coder:30b (lokal, 19GB Q4_K_M) oder magicoder:7b (lokal, 4GB, 60+ Tokens/Sek.)
```

### Beispiel-Ausgabe (JSON)
```json
{
  "file": "service.py",
  "language": "python",
  "smells": [
    {
      "type": "long_method",
      "location": {
        "file": "service.py",
        "start_line": 42,
        "end_line": 67
      },
      "description": "Methode process_data() hat 25 Zeilen und zu viele Verantwortlichkeiten",
      "severity": "high",
      "suggestion": "Extrahiere Zeilen 45-58 in eine neue Methode validate_input(). Beispiel:\n\n    def validate_input(data):\n        # Validierungslogik hier\n        pass\n\n    def process_data(data):\n        if validate_input(data):\n            # Rest der Logik",
      "reason": "Verstößt gegen Single Responsibility Principle und ist schwer testbar",
      "impact": "maintainability"
    },
    {
      "type": "duplicate",
      "location": {
        "file": "service.py",
        "start_line": 12,
        "end_line": 15
      },
      "description": "Identischer Code in format_response() und format_output()",
      "severity": "medium",
      "suggestion": "Extrahiere den gemeinsamen Code in eine Methode format_common(). Beispiel:\n\n    def format_common(data):\n        # Gemeinsame Formatierungslogik\n        pass\n\n    def format_response(data):\n        return format_common(data)\n\n    def format_output(data):\n        return format_common(data)",
      "reason": "Verstößt gegen DRY-Prinzip (Don't Repeat Yourself)",
      "impact": "maintainability"
    }
  ],
  "stats": {
    "total_smells": 2,
    "high": 1,
    "medium": 1,
    "low": 0,
    "coverage": "85%"
  }
}
```
