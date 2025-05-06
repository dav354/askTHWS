# Rechtssicherer Chatbot: Hybrid-Architektur mit Knowledge Graph und Vektordatenbank (Python)

## 1. Einleitung

Ein rechtssicherer Chatbot sollte verifizierte Informationen liefern. Durch die Kombination eines Knowledge Graphen (strukturierte, nachvollziehbare Fakten) mit einer Vektordatenbank (semantische Suche in unstrukturierten Texten) entsteht ein System, das fundierte und erklärbare Antworten gibt.

## 2. Grundlagen – Was ist ein Knowledge Graph?

Ein Knowledge Graph ist ein Netzwerk aus Entitäten und deren Beziehungen. Er ermöglicht präzise, kontextreiche und erklärbare Antworten. Vorteile:

- **Semantische Abfragen** über komplexe Zusammenhänge
- **Konsistenz** durch zentralisierte Faktenbasis
- **Erklärbarkeit** durch transparente Bezüge
- **Wiederverwendbarkeit** in mehreren Szenarien

Herausforderung: Der initiale Aufbau ist aufwendig und benötigt domänenspezifisches Wissen.

## 3. Warum eine Vektordatenbank?

Vektordatenbanken ermöglichen die Suche in unstrukturierten Daten durch semantische Ähnlichkeit. Sie ergänzen Knowledge Graphen, indem sie z. B. freiformulierte Fragen mit passenden Dokumentausschnitten verbinden.

Die hybride Architektur nutzt:

- **Graph** für verlässliche Fakten
- **Vektor-DB** für Kontext und erklärende Inhalte

Gemeinsam liefern sie genaue und gleichzeitig flexible Antworten.

## 4. Technische Architektur (Python)

Bestandteile:

- **Knowledge Graph (z. B. Neo4j, RDFLib)**
- **Vektordatenbank (z. B. Weaviate, Qdrant)**
- **LLM (z. B. OpenAI, Llama)**
- **Frameworks (z. B. LangChain)**

Ablauf:

1. Nutzerfrage wird analysiert
1. Relevante Knoten im Graph abgefragt
1. Semantische Suche in Textdaten
1. Kombination beider Ergebnisse in ein Prompt
1. Antworterstellung durch LLM
1. Ausgabe mit optionalem Quellenverweis

## 5. Anbieter und Tools

- **Graph-Datenbanken:** Neo4j, GraphDB, Stardog
- **Vektordatenbanken:** Weaviate, Qdrant, Pinecone, FAISS
- **Python-Frameworks:** LangChain, LlamaIndex

Alle Tools sind kombinierbar und teilweise open source.

## 6. Best Practices

- **Pflege & Aktualität** der Inhalte
- **Transparenz & Datenschutz** beachten (DSGVO!)
- **Promptdesign:** Fakten als unveränderlich kennzeichnen
- **Stakeholder einbinden** (z. B. Recht, IT, Beratung)
- **Feedback-Schleifen** für Qualitätssicherung

## 7. Fazit & Ausblick

Die Kombination aus Knowledge Graph und Vektordatenbank ermöglicht rechtlich abgesicherte, nachvollziehbare und leistungsfähige Chatbots. Sie eignet sich besonders für Hochschulen, Behörden oder juristische Bereiche. Mit zunehmender Tool-Reife wird der Einstieg einfacher und der Nutzen größer. Der Aufwand lohnt sich – besonders dort, wo Vertrauen zählt.

## Automatisierter Knowledge Graph aus fiw.thws.de – Kompaktübersicht

### 1. Einleitung

Ein Knowledge Graph auf Basis der Website fiw.thws.de kann Informationen zu Studiengängen, Modulen, Personen und Fristen strukturiert bereitstellen. Ziel: Chatbots, Navigation und semantische Suche verbessern. Automatisierung ist essenziell, um aktuelle, konsistente Daten bei minimalem Pflegeaufwand zu gewährleisten.

### 2. Was ist ein Website-Knowledge Graph?

Ein Website-Knowledge Graph wandelt Webinhalte in vernetzte Entitäten um. Beispiel-Knoten: Studiengänge, Module, Personen, Termine. Relationen: "leitet", "enthält Modul", "hat Frist". Vorteil: Kontextreiche, maschinenlesbare Struktur.

### 3. Warum Automatisierung?

- Aktuelle Website ≠ aktueller Graph → Automatisierung erkennt Änderungen
- Delta-Erkennung & Validierung = nur echte Neuerungen werden übernommen
- Wartungsarm und skalierbar

### 4. Technische Architektur (Python-basiert)

**Pipeline:**

1. **Crawler** (Scrapy/Playwright): durchforstet fiw.thws.de
1. **Parser** (BeautifulSoup): extrahiert Inhalte (z. B. Studiengänge, Module)
1. **NLP** (spaCy/OpenIE): erkennt Entitäten & Relationen in Text
1. **Mapping** zu Ontologie: wandelt Daten in vordefinierte Struktur
1. **Tripel-Erzeugung** (RDFLib/Neo4j): baut den Graph
1. **Speicherung** (GraphDB/Neo4j): macht Daten durchsuchbar
1. **Validierung** (pySHACL): sichert Datenqualität

### 5. Tools & Bibliotheken

- **Crawler:** Scrapy, Playwright
- **Parser:** BeautifulSoup
- **NLP:** spaCy, Transformers, OpenIE
- **Graph-Erzeugung:** RDFLib, Neo4j, GraphDB
- **Validierung:** pySHACL
- **Mapping-Hilfe:** Karma, SKOS

### 6. Empfehlungen

- MVP starten (z. B. Studiengänge + Ansprechpartner)
- Klar definierte Ontologie verwenden
- Monitoring & Delta-Erkennung einbauen
- Zusammenarbeit mit Redakteuren (Rückkopplung)
- DSGVO beachten: keine unkontrollierte Nutzung von Personendaten

### 7. Fazit & Ausblick

Ein automatisierter Graph aus fiw.thws.de ist machbar. Vorteile: konsistente Datenbasis für Chatbots & QA, weniger Redaktionsaufwand. Nächste Schritte: kontinuierliche Aktualisierung, semantische Suche, RAG-Integration (Graph + LLM).
