# Vektordatenbanken im Projekt

## 1. Einleitung

- **Kontext:**
  Wir planen, Vektordatenbanken vor allem für unsere semantische Suche einzusetzen. Im Gegensatz zu klassischen Datenbanken ermöglichen Vektordatenbanken eine kontextbezogene (semantische) Suche, die über reine Schlüsselwortabfragen hinausgeht.

- **Relevanz:**
  Klassische relationale Datenbanken stoßen schnell an ihre Grenzen, wenn es um die Suche nach Ähnlichkeiten und Kontexten in unstrukturierten Daten (z. B. Text, Audio, Bilder) geht. Eine Vektordatenbank löst diese Herausforderungen, indem sie Daten in Form von numerischen Vektoren speichert und schnelle Ähnlichkeitssuchen ermöglicht.

______________________________________________________________________

![INSER/SELCT V-DB](/assets/vectordatabase.jpg)

______________________________________________________________________

## 2. Grundlagen / Was ist eine Vektordatenbank?

- **Definition:**
  Eine Vektordatenbank ist eine Datenbank, die sich auf das Speichern und Abfragen hochdimensionaler Vektoren spezialisiert. Typischerweise handelt es sich um Embeddings, die mithilfe von KI-Modellen aus verschiedensten Datentypen (Text, Bild, Audio) erzeugt werden.

- **Funktionsprinzip:**

  - **Vektor-Repräsentationen (Embeddings)**: KI-Modelle (z. B. Transformer-Netzwerke wie BERT oder GPT) wandeln Eingaben (z. B. Sätze, Bilder) in numerische Vektoren um.
  - **Ähnlichkeitssuche**: Anstatt nach exakten Übereinstimmungen zu suchen, prüft die Datenbank, welche Vektoren sich in einem hochdimensionalen Raum ähneln. Dazu werden Verfahren wie „Nearest Neighbor Search“ eingesetzt, oft in Form von Approximate Nearest Neighbor (ANN).

- **Abgrenzung zu klassischen Datenbanken:**
  Relationale Datenbanken (z. B. MySQL, PostgreSQL) sind auf strukturierte Tabellen ausgerichtet und bieten sich nicht für Ähnlichkeitssuchen in hochdimensionalen Vektorräumen an. Vektordatenbanken ermöglichen hingegen, semantische Beziehungen zwischen Datenpunkten zu erkennen und schnell zu vergleichen.

______________________________________________________________________

## 3. Warum eine Vektordatenbank für unser Projekt?

- **Use Cases im Projekt:**

  - Semantische Suche in FAQs, Dokumenten, Studienordnungen etc.
  - Kontextsensitive Antworten im Chatbot (z. B. verschiedene Formulierungen oder Synonyme erkennen).
  - Clustering thematisch ähnlicher Beiträge oder Dokumente.

- **Vorteile im Vergleich zu Alternativen:**

  - **Einfachere KI-Workflows**: Da Embeddings in Vektordatenbanken direkt abgefragt werden können, entfallen komplizierte Umwege oder Workarounds.
  - **Schnellere und genauere Suchergebnisse**: Insbesondere, wenn die Abfragen nicht eindeutig sind, liefert die semantische Suche häufig relevantere Treffer als reine Schlagwortsuche.
  - **Skalierbarkeit**: Moderne Vektordatenbanken sind auf große Datenmengen optimiert.

- **Konkretes Beispiel im Projekt:**
  Wird eine Anfrage wie „Wie bewerbe ich mich für ein Studium?“ gestellt, kann die semantische Suche nicht nur Dokumente mit den Begriffen „bewerben“ und „Studium“ identifizieren, sondern auch Texte, die sich inhaltlich mit der Thematik beschäftigen („Immatrikulation“, „Einschreibung“, „Zulassungsvoraussetzungen“ etc.).

______________________________________________________________________

## 4. Technische Grundlagen und Architektur

- **Aufbau und Indexierung:**

  - **Datenspeicherung:** Vektoren werden meist in speziellen Strukturen abgelegt, die auf Ähnlichkeitssuche optimiert sind (z. B. HNSW, IVF, PQ).
  - **ANN-Algorithmen**: Approximate Nearest Neighbor (ANN) akzeptiert leichte Ungenauigkeiten in der Ergebnismenge, ermöglicht dafür aber deutlich höhere Abfragegeschwindigkeiten.

- **Daten-Workflow:**

  - **Embeddings erzeugen**: Ein KI-Modell wandelt Text in Vektoren um.
  - **Einfügen in die Datenbank**: Die Vektoren werden zusammen mit Metadaten (Titel, ID etc.) gespeichert.
  - **Abfrage**: Bei einer Suchanfrage wird ebenfalls ein Embedding erzeugt und nach den Vektoren mit der größten Ähnlichkeit gesucht.

- **Integration mit anderen Systemen:**

  - **APIs und SDKs**: Viele Vektordatenbanken bieten REST- oder gRPC-Schnittstellen, manchmal auch Python-SDKs.
  - **Projektarchitektur**: Die Vektordatenbank kann direkt an unseren Chatbot angebunden werden. Das Frontend leitet die Suchanfrage an den Chatbot weiter, der wiederum Embeddings erzeugt und eine Anfrage an die Vektordatenbank stellt.

______________________________________________________________________

## 5. Anbieter und Lösungen

### 5.1 Open-Source-Lösungen

- **Qdrant**

  - **Vorteile**: Hohe Performance, leichtgewichtig und in Rust entwickelt, dadurch ressourcenschonend
  - **Nachteile**: Noch relativ jung auf dem Markt, daher weniger etablierte Best Practices

- **FAISS (Facebook AI Similarity Search)**

  - **Vorteile**: Sehr performante Bibliothek für ähnliche Abfragen, gut für Forschungszwecke und skalierbare Systeme.
  - **Nachteile**: Keine „fertige“ Datenbank, eher ein Toolkit (v. a. für Python).

- **Haystack (deepset)**

  - **Vorteile**: Framework für kontextuelle Suche, beinhaltet Vektor-Suche und Pipeline-Management.
  - **Nachteile**: Häufig eher Teil einer größeren NLP-Lösung als eine reine Vektordatenbank.

### 5.2 Cloud/Managed Services

- **Pinecone**

  - **Vorteile**: Vollständig gemanagter Dienst, einfacher Einstieg, Skalierbarkeit auf Knopfdruck.
  - **Nachteile**: Kosten und Vendor-Lock-in (Monatsgebühr, proprietäre Infrastruktur).

- **Weaviate**

  - **Vorteile**: Open Source und Managed-Version, flexible Schema-Struktur, Graph-basierter Ansatz.
  - **Nachteile**: Noch relativ jung, Dokumentation ist zwar umfangreich, aber teils lückenhaft.

- **Azure Cognitive Search (mit Vektor-Suche)**

  - **Vorteile**: Direkt in das Azure-Ökosystem eingebunden, simpel für bestehende Azure-Kunden.
  - **Nachteile**: Teilweise eingeschränkte Konfigurationsmöglichkeiten, Vendor-Lock-in.

- **Elasticsearch mit Vektor-Suche**

  - **Vorteile**: Weit verbreitet, bereits bekanntes Such-Tool, große Community.
  - **Nachteile**: Bei sehr hohem Datenvolumen oder besonders hohen Dimensionalitäten kann die Performance schwächeln.

### 5.3 Kriterien für die Auswahl

1. **Performance und Skalierung**: Wichtig bei großen Datenmengen und Echtzeitanwendungen.
1. **Kostenmodell**: Open Source vs. kommerziell, laufende Betriebs- und Wartungskosten.
1. **Integrationsmöglichkeiten**: APIs, Programmiersprachen, Cloud vs. On-Premise.
1. **Community und Dokumentation**: Support, Tutorials, Hilfestellungen.

## Begründung für die Wahl von Qdrant

Wir haben uns entschieden, in unserem Projekt **Qdrant** als Vektordatenbank einzusetzen, weil sie einerseits eine hohe Performance bei Ähnlichkeitssuchen bietet und andererseits durch ihre Implementierung in Rust sehr ressourcenschonend ist. Außerdem ist Qdrant open source und lässt sich relativ einfach in unser Projekt integrieren.

______________________________________________________________________

## 6. Best Practices und Empfehlungen

- **Datenvorbereitung (Feature Engineering):**

  - Wähle hochwertige Embedding-Modelle.
  - Standardisiere deine Daten: Tokenisierung, Normalisierung und ggf. Entfernung von Stop-Wörtern.

- **Index-Tuning:**

  - Wähle den passenden Index-Algorithmus je nach Datenmenge und Performancebedarf.
  - Teste unterschiedliche Parameter (z. B. Anzahl Nachbarn, Größe von Clustern), um das Optimum für deinen Anwendungsfall zu finden.

- **Skalierung und Hosting:**

  - **Horizontal**: Sharding großer Datensätze auf mehrere Knoten.
  - **Vertikal**: Ausreichend RAM, CPU/GPU-Kapazitäten bereitstellen, um Suchanfragen schnell zu bearbeiten.

- **Security und Datenschutz:**

  - Verschlüssele Daten im Ruhezustand und bei der Übertragung (TLS).
  - Setze Rollen- und Zugriffsrechte auf, um unbefugte Zugriffe zu verhindern.
  - Stelle sicher, dass beim Speichern von Texten DSGVO-Vorgaben eingehalten werden, insbesondere wenn personenbezogene Daten involviert sind.

______________________________________________________________________

## 8. Fazit und Ausblick

- **Zusammenfassung**:
  Vektordatenbanken sind ein leistungsfähiges Werkzeug, um große Mengen unstrukturierter Daten mittels semantischer Suche schnell zu durchsuchen. Sie bieten deutliche Vorteile gegenüber klassischen Datenbanken, wenn es um kontextuelles Auffinden und Kategorisieren geht.
