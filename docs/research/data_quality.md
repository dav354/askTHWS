# Datenqualität

Um den Fortschritt und die Datenqualität des Scrapers zu bestimmen, hier verschiedene Kategorien an denen man die Qualität der Daten zwischen den verschiedenen Runs/Versionen beurteilen kann.

## 📁 Allgemeine Übersicht

- Anzahl der Einträge insgesamt
- Anzahl einzigartiger URLs
- Anzahl pro Subdomain
- Anzahl pro `type`: html, pdf, ical
- Neue vs. entfernte URLs zwischen zwei Runs

## 🧹 Textqualität

- Durchschnittliche Textlänge (Zeichen oder Wörter)
- Median und maximale Textlänge
- Anzahl leerer oder sehr kurzer Texte (z. B. < 20 Zeichen)
- Duplikate im Textinhalt (gleiche Texte bei verschiedenen URLs)

## 🏷️ Metadatenqualität

- Anteil der Einträge mit leerem oder fehlendem `title`
- Anteil der Einträge mit fehlendem `date_updated`
- Anteil der Einträge mit gültigem `date_updated`-Format (ISO 8601)

## 🔁 Veränderungen im Vergleich

- Mehr oder weniger gefundene Seiten?
- Hat sich die Textlänge verbessert (länger = oft besser)?
- Hat sich die Anzahl erkannter Datumsfelder verbessert?
- Gibt es neue Duplikate oder wurden welche entfernt?

# ✅ Nutzung

```bash
# Einzelnen Run analysieren
python3 compare_scraping_result.py run.json

# Zwei Runs vergleichen
python3 compare_scraping_result.py run1.json run2.json

# Mit Änderungsanzeige (kompakt)
python3 compare_scraping_result.py run1.json run2.json -v

# Mit Änderungsanzeige (detailliert)
python3 compare_scraping_result.py run1.json run2.json -vv
```
