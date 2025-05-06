# Webscraping-Bibliotheken

## 1. BeautifulSoup

- Sehr einfach zu benutzen
- Ideal für kleinere Scraping-Aufgaben
- Arbeitet gut mit `requests`
- Kein Browser, also kein JavaScript-Support

## 2. Scrapy

- Vollständiges Framework für große Scraping-Projekte
- Sehr schnell und asynchron
- Unterstützt Pipelines, Middleware, Auto-Throttling
- Steilere Lernkurve als BeautifulSoup

## 3. Selenium

- Simuliert einen echten Browser
- Ideal für Seiten mit viel JavaScript
- Kann mit Headless-Browsern wie Chrome oder Firefox laufen
- Langsamer als andere Tools

## 4. Playwright (mit Python)

- Modernes, schnelles und stabiles Tool zur Browserautomation
- Besseres Handling von JavaScript als Selenium
- Unterstützt mehrere Browser (Chrome, Firefox, Safari)

______________________________________________________________________

# PDF-Bibliotheken

## 1. PyMuPDF (`fitz`)

- Schnelles, zuverlässiges Parsing von PDFs
- Kann Text aus Seiten extrahieren (`page.get_text()`), auch strukturiert
- Eignet sich sehr gut für Scraping-Zwecke

## 2. pdfminer.six

- Sehr detailliert, aber langsamer
- Gut für strukturierte Layout-Extraktion (z. B. Tabellen)
- Komplexere API

## 3. PyPDF2 / pypdf

- Gut zum Zusammenfügen, Seiten extrahieren, Metadaten
- Eher für Manipulation als fürs reine Textlesen

Empfohlen wird hier `PyMuPDF`, da schnell und einfach nutzbar.

______________________________________________________________________

# HTML-Parser

## 1. BeautifulSoup

- Flexibel, einfach, unterstützt CSS-Selektoren und einfache Tree-Navigation

## 2. lxml

- Sehr schnell, mit vollem XPath-Support
- Ideal bei großen HTML-Mengen oder wenn XPath benötigt wird

## 3. Scrapy Selectors

- Native Unterstützung von CSS und XPath
- Sehr performant im Scrapy-Kontext (`response.css()` / `response.xpath()`)

______________________________________________________________________

# Auswahlkriterien

- **Performance**: möglichst schnell, auch bei großen Datenmengen

- **Respektiert robots.txt**

  <details>
    <summary>robots.txt der THWS Seite</summary>

  ```txt
  User-agent: *

  Allow: /fileadmin/template2016/

  Disallow: /cgi-bin/
  Disallow: /fileadmin/
  Disallow: /uploads/
  Disallow: /uploads/tx_odspmpdf/
  Disallow: /personen/

  Disallow: /*.swf$
  Disallow: /*.gif$
  Disallow: /*.jpg$
  Disallow: /*.png$

  ```

- **HTML-Parsing-Fähigkeiten**

- **Duplikatvermeidung**

- **Support für PDFs und iCal-Dateien**

______________________________________________________________________

# Begründung der Auswahl

Scrapy ist sehr einfach aufzusetzen mit `scrapy startproject thws-scraper .` und resperktiert mit der gesetzten config `ROBOTSTXT_OBEY = True` auch die `robots.txt`. Ebenso lässt sich hier auch direkt ist auch direkt mit den scrapy selectors html parsing verfügbar. Die PDFs lassen sich mit PyMuPDF verarbeiten.

______________________________________________________________________

# JSON Struktur

```json
  "url": "https://www.thws.de/beispiel",
  "type": "html | pdf | ical",
  "title": "Titel",
  "text": "Gescrapter Text",
  "date_scraped": "2025-04-06T12:34:56",
  "date_updated": "2024-12-01 | null"
```

# Scrapy Settings

## Einstellungen

| Einstellung | Beschreibung |
|---------------------------|------------------------------------------------------------------------------|
| `ROBOTSTXT_OBEY = True` | Respektiert die `robots.txt` der Seite |
| `DOWNLOAD_DELAY = 0.5` | Pausiert 0,5 Sekunden zwischen Requests, um Server zu schonen |
| `AUTOTHROTTLE_ENABLED` | Passt das Crawling automatisch an (z. B. bei langsamen Seiten) |
| `CONCURRENT_REQUESTS = 16`| Führt bis zu 16 Requests gleichzeitig aus |
| `USER_AGENT` | Identifiziert den Crawler höflich und transparent |
