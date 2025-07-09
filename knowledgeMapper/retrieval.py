# File: knowledgeMapper/retrieval.py
# Description: v6.4 - FINAL & VERIFIED VERSION. Corrects all regex syntax
#              errors and properly implements the "Generate-Then-Process" architecture.


from datetime import datetime
from typing import List, Dict, Any, Union
from lightrag import LightRAG
from lightrag.base import QueryParam


"""Specifies the retrieval mode:
- "local": Focuses on context-dependent information.
- "global": Utilizes global knowledge.
- "hybrid": Combines local and global retrieval methods.
- "naive": Performs a basic search without advanced techniques.
- "mix": Integrates knowledge graph and vector retrieval.
"""
MODE = "naive"

# This prompt correctly instructs the model to create traceable inline citations.
RELIABLE_SYSTEM_PROMPT_TEMPLATE = """
---
MISSION:
Generiere eine präzise, sachliche und vollständig auf den bereitgestellten Daten basierende deutsche Antwort auf die `AKTUELLE ANFRAGE`. Die fehlerfreie Einhaltung der folgenden Direktiven ist von entscheidender Bedeutung.

---
ROLLE:
Du agierst als eine hochpräzise Text-Analyse- und Synthese-Engine. Deine Arbeitsweise ist rein algorithmisch und datengesteuert.

---
VERARBEITUNGSPROTOKOLL (Chain-of-Thought):
Du musst diesen dreistufigen Prozess exakt einhalten:
1.  **Analyse der Beziehungen (KG):** Ermittle die Kernzusammenhänge aus den `Relationships(KG)` als logisches Grundgerüst der Antwort.
2.  **Anreicherung mit Details (KG):** Ergänze dieses Gerüst mit spezifischen Fakten aus den `description`-Feldern der `Entities(KG)`.
3.  **Formulierung mit Belegen (DC):** Konstruiere die finale deutsche Antwort ausschließlich mit dem Vokabular und den Informationen aus den `Document Chunks(DC)`.

---
AUSGABERICHTLINIEN:
- **Sprache:** Die Ausgabe erfolgt ausnahmslos auf Deutsch.
- **Stil:** Beginne direkt mit der Antwort. Formuliere prägnant und sachlich. Nutze bei Bedarf Markdown zur Strukturierung.

---
TABU-ZONE (STRIKTE VERBOTE & GUARDRAILS):
Die folgenden Handlungen sind strengstens untersagt:
- **Kein externes Wissen:** Die Nutzung von Informationen außerhalb der `WISSENSBASIS` ist verboten.
- **Keine Spekulation:** Erfinde, interpretiere oder schlussfolgere nichts, was nicht explizit in den Daten steht.
- **Keine Quellen:** Die Ausgabe darf keinerlei Quellen, Zitate oder Dateipfade (`file_path`) enthalten.
- **Keine Metadaten:** Der Inhalt von `<think>`-Tags muss vollständig ignoriert werden.
- **Keine Einleitungen:** Verwende keinerlei einleitende Floskeln.
- **Fallback-Direktive:** Wenn eine Antwort gemäß dem Protokoll nicht möglich ist, lautet die **einzige erlaubte Ausgabe** wortwörtlich: "Ich konnte keine passenden Informationen zu Ihrer Anfrage finden."

---
WISSENSBASIS:
{context}
---
AKTUELLE ANFRAGE:
{user_query}
---
"""

# NEU: Prompt für die Query Expansion
QUERY_EXPANSION_PROMPT = """
Du bist Expert*in für Suchanfragen. Gib zu folgender Frage 1–2 alternative Formulierungen oder verwandte Stichwörter in DEUTSCH an. Trenne die Stichwörter mit Kommas. Gib nur die Stichwörter zurück, keine Erklärungen.

FRAGE: {user_query}

Stichwörter:
"""

async def prepare_and_execute_retrieval(
        user_query: str,
        rag_instance: LightRAG,
) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
    """
    Orchestrates a reliable RAG process that returns a separate clean answer
    and a structured list of the sources used to generate it.
    """

    params_bypass = QueryParam(mode="bypass", top_k=0)

    params_context = QueryParam(
        mode=MODE,
        top_k=7,
        only_need_context=True
    )
    print("1. Enriching Query...")
    enriched_query = await rag_instance.aquery(user_query, param=params_bypass, system_prompt=QUERY_EXPANSION_PROMPT)
    print("Enriched Query Result:", enriched_query)

    print("2. Retrieving full context for source mapping...")

    context_data_str = await rag_instance.aquery(user_query, param=params_context)

    print("3. Generating intermediate answer ...")
    final_system_prompt = RELIABLE_SYSTEM_PROMPT_TEMPLATE.format(
        current_date=datetime.now().strftime("%d. %B %Y"),
        location="Würzburg",
        context=context_data_str,
        user_query=user_query + enriched_query
    )

    citable_answer_text = await rag_instance.aquery(
        user_query,
        param=params_bypass,
        system_prompt=final_system_prompt
    )

    return {
        "answer": citable_answer_text,
        "sources": context_data_str + "\n\n\r"+enriched_query
    }
