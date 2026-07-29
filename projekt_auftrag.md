# Projektauftrag 5 - KI-gestütztes Refactoring

Codequalität verbessern und Verhalten durch Tests absichern

---

## 1. Projektbezeichnung

KI-gestütztes Refactoring einer bestehenden Anwendungskomponente mit Vorher-Nachher-Tests und nachvollziehbarer Änderungsdokumentation.

---

## 2. Auftraggeber

CampusCode Software GmbH

---

## 3. Auftragnehmer

Projektgruppe KI-Anwendungsentwicklung

---

## 4. Projektbeschreibung

In einer bestehenden Anwendung enthält eine zentrale Serviceklasse eine lange Methode mit Duplikaten, unklaren Namen und vermischten Verantwortlichkeiten. Änderungen sind dadurch fehleranfällig und schwer testbar.

Ein KI-Codeassistent soll Refactoring-Vorschläge erzeugen. Die Fachkraft entscheidet, welche Änderungen übernommen werden. Das beobachtbare Verhalten der Komponente darf sich nicht verändern.

Vor dem Refactoring müssen automatisierte Charakterisierungs- und Unit-Tests vorhanden sein. Nach jeder Änderung werden Tests, Linting, Security-Checks und Code Review durchgeführt. Alle Prompts, Entscheidungen und Änderungen bleiben über die Versionskontrolle nachvollziehbar.

---

## 5. Projektziel

Ziel ist eine besser strukturierte, wartbare Komponente mit unverändertem fachlichem Verhalten und prüfbarem Qualitätsnachweis.

- Auswahl einer begrenzten Legacy-Komponente mit erkennbarem Refactoring-Bedarf
- Beschreibung des bestehenden Verhaltens und relevanter Risiken
- Erstellung oder Ergänzung automatisierter Vorher-Tests
- versionierte Prompts für Analyse und Refactoring-Vorschläge
- schrittweise Umsetzung mit kleinen Commits
- Nachweis durch Tests, Linting, Review und Qualitätskennzahlen
- Dokumentation übernommener und verworfener KI-Vorschläge

---

## 6. Wirtschaftliche und organisatorische Rahmenbedingungen

Für die Umsetzung steht ein fiktives Budget von 1.000 Euro zur Verfügung.

- Komponente mit höchstens 250 Zeilen produktivem Code
- keine Veränderung öffentlicher Schnittstellen ohne begründete Freigabe
- keine Secrets oder vertraulichen Quelltexte an nicht freigegebene Dienste
- jeder Refactoring-Schritt muss rückgängig machbar sein
- Tests müssen vor und nach der Änderung erfolgreich laufen
- menschliches Code Review ist verpflichtend

---

## 7. Projektumfang

Der Auftrag umfasst folgende Arbeitsschritte:

### Analysephase
- Code Smells, Verantwortlichkeiten und Abhängigkeiten erfassen
- bestehendes Verhalten und fehlende Tests dokumentieren
- Qualitätsziele und Nicht-Ziele festlegen

### Planungsphase
- Refactoring-Schritte und Rückfallstrategie planen
- Promptvorlage und Reviewkriterien definieren
- Messgrößen wie Komplexität, Duplikate und Testabdeckung festlegen

### Realisierungsphase
- Charakterisierungstests ergänzen
- KI-Vorschläge erzeugen und fachlich bewerten
- Änderungen schrittweise umsetzen und versionieren
- Namen, Funktionen und Verantwortlichkeiten verbessern

### Testphase
- Vorher-Nachher-Tests ausführen
- Linting, Formatierung und Security-Checks durchführen
- Regressionen und Performanceabweichungen prüfen
- Code Review und Korrekturen dokumentieren

### Abschlussphase
- Qualitätskennzahlen vergleichen
- übernommene und verworfene Vorschläge begründen
- Lessons Learned und nächste Schritte präsentieren

---

## 8. Projektumfeld

- kleines Legacy-Beispielprojekt in einer gängigen Programmiersprache
- Unit-Test-Framework, Linter und statische Analyse
- lokales Git-Repository mit Branch- und Review-Prozess
- optional freigegebener KI-Codeassistent
- keine Produktivdaten und keine produktive Bereitstellung

---

## 9. Projektzeit

Für die Durchführung des Projektes stehen 16 Unterrichtsstunden zur Verfügung.

---

## 10. Erwartete Projektergebnisse

- Beschreibung der Ausgangskomponente und ihrer Code Smells
- Vorher-Tests und dokumentiertes Referenzverhalten
- Prompt- und Vorschlagsprotokoll
- refaktorierte, getestete Komponente mit nachvollziehbaren Commits
- Test-, Linting-, Security- und Review-Nachweise
- Vergleich von Komplexität, Duplikaten und Testabdeckung
- Kurzbericht mit Risiken, verworfenen Vorschlägen und Lessons Learned
