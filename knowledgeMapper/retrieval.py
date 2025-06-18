# File: knowledgeMapper/retrieval.py
# Description: v6.10 - FIX FOR EMPTY CONTEXT. Handles empty string from aquery(only_need_context=True)

import re
import ast
from datetime import datetime
from typing import List, Dict, Any, Union
from lightrag import LightRAG
from lightrag.base import QueryParam
from knowledgeMapper.local_models import OllamaLLM

MODE = "mix"

# This prompt correctly instructs the model to create traceable inline citations.
RELIABLE_SYSTEM_PROMPT_TEMPLATE = """
**SYSTEMBEFEHL FÜR PRÄZISE WISSENSBASIERTE ANTWORTEN:**
1.  **SPRACHE:** Antworte **AUSSCHLIESSLICH** auf **DEUTSCH**.

2.  **INFORMATIONSEINSCHRÄNKUNG & KONTEXTTREUE:** Deine Antwort MUSS **VOLLSTÄNDIG** und **AUSSCHLIESSLICH** auf den Informationen im bereitgestellten `KONTEXT` basieren.
    * **Priorisierung von Beziehungen (KG) und Entitätsdetails (DC):** Nutze zunächst die Informationen aus dem `Relationships(KG)`-Abschnitt, um direkte Verbindungen zwischen Entitäten zu identifizieren. Ergänze diese Informationen mit den Beschreibungen der Entitäten aus den `Document Chunks(DC)`.
    * **KEINE Halluzinationen:** Generiere **KEINE** neuen Informationen, spekuliere **NICHT** und füge **NICHTS HINZU**, was nicht im `KONTEXT` explizit genannt ist. Dies beinhaltet auch die Verknüpfung von Informationen, die im Kontext nicht direkt miteinander verbunden sind (z.B. geografische Nähe ohne explizite Verbindungsbeschreibung).
    * **Umgang mit unbekannten Begriffen/fehlenden direkten Verknüpfungen:** Wenn der `KONTEXT` eine Abkürzung, Domänen-Slang, einen Fachbegriff oder eine Entität (z.B. einen spezifischen Gebäudecode wie "SHL") enthält, dessen Bedeutung oder deren direkte Beziehung zu anderen relevanten Konzepten (z.B. Buslinien) nicht direkt im `KONTEXT` erklärt oder verknüpft wird, **dann verwende den Begriff genau so, wie er im Kontext steht, und versuche NICHT, ihn zu erklären, zu interpretieren oder nicht explizit genannte Verbindungen herzustellen.** Halluziniere KEINE Bedeutungen, Annahmen oder implizite geografische oder funktionale Verknüpfungen.
    * **Zitierungspflicht:** Füge am Ende JEDES Satzes oder Absatzes, der Informationen aus dem `KONTEXT` verwendet, die **ID der Quelle in Klammern** hinzu, z.B. (DC-ID: 1) oder (KG-ID: 5). Wenn Informationen aus mehreren Quellen in einem Satz oder Absatz kombiniert werden, nenne alle relevanten IDs (DC-ID: 1, KG-ID: 5).

3.  **PRÄZISION & KONSISTENZ:**
    * Synthetisiere relevante Fakten aus den `Relationships(KG)`- und `Document Chunks(DC)`-Abschnitten zu einer **flüssigen, kohärenten und gut lesbaren Antwort**.
    * Wenn der `KONTEXT` widersprüchliche Informationen zu einem Thema enthält, gib **BEIDE Versionen an** und nenne die jeweiligen Quell-IDs.

4.  **FALLBACK-PROZEDERE:** Falls die `NUTZERFRAGE` **NICHT** oder **NICHT ausreichend** im `KONTEXT` beantwortet werden kann und **auch keine indirekten, zitierfähigen Informationen** (weder aus DC noch aus KG) vorhanden sind, antworte **AUSSCHLIESSLICH** und wortwörtlich mit:
    "Ich konnte keine passenden Informationen zu Ihrer Anfrage in meiner Wissensdatenbank finden."
    Verändere diese Formulierung **NICHT**.

5.  **UNTERDRÜCKUNG VON PLAPPERN/ERGÄNZUNGEN:** Gehe direkt zur Antwort über. Vermeide einleitende Phrasen wie "Basierend auf dem Kontext..." oder abschließende Bemerkungen. Die Antwort soll **NUR** die Beantwortung der Nutzerfrage sein.

---
**ZUSATZDATEN:**
- Heutiges Datum: {current_date}
- Standort: {location}
---
**KONTEXT:**
{context}
**NUTZERFRAGE:**
{user_query}
"""


async def prepare_and_execute_retrieval(
        user_query: str,
        rag_instance: LightRAG,
) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
    """
    Orchestrates a reliable RAG process that returns a separate clean answer
    and a structured list of the sources used to generate it.
    """

    params_context = QueryParam(
        mode=MODE,
        top_k=15,
        only_need_context=True
    )
    print("2. Retrieving full context for source mapping...")

    context_data_str = await rag_instance.aquery(user_query, param=params_context)

    # --- 1. Generate the Intermediate Answer with Inline Citations ---
    print("1. Generating intermediate answer with inline citations...")
    final_system_prompt = RELIABLE_SYSTEM_PROMPT_TEMPLATE.format(
        current_date=datetime.now().strftime("%d. %B %Y"),
        location="Würzburg",
        context=context_data_str,
        user_query=user_query
    )
    params = QueryParam(mode="bypass", top_k=0)

    citable_answer_text = await rag_instance.aquery(
        user_query,
        param=params,
        system_prompt=final_system_prompt
    )
    print("   - Intermediate citable answer received.")

    # --- 2. Retrieve the Full Context for Source Lookup ---
    print("2. Retrieving full context for source mapping...")

    print("   - Raw context data received.")

    print("   - Structured source list created.")

    return {
        "answer": citable_answer_text,
        "sources": context_data_str
    }
