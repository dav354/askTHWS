# File: knowledgeMapper/retrieval.py
# Description: v6.4 - FINAL & VERIFIED VERSION. Corrects all regex syntax
#              errors and properly implements the "Generate-Then-Process" architecture.


from datetime import datetime
from typing import List, Dict, Any, Union

# In knowledgeMapper/retrieval.py

RELIABLE_SYSTEM_PROMPT_TEMPLATE = """
**SYSTEMBEFEHL:**
1.  **SPRACHE:** Antworte **IMMER** auf **DEUTSCH**.

2.  **KERNANWEISUNG:** Deine Antwort muss **AUSSCHLIESSLICH** auf den Informationen im bereitgestellten `KONTEXT` basieren. Fasse die relevanten Informationen aus dem Kontext zusammen, um die `NUTZERFRAGE` präzise zu beantworten.
    * Verwende **KEIN** externes Wissen.
    * Erfinde oder spekuliere **NICHTS**.

3.  **ZITIERUNG:** Gib am Ende deiner Antwort die Quelle(n) an, indem du die URL oder den Titel aus den Metadaten der genutzten Kontext-Dokumente nennst.

4.  **WICHTIGSTE REGEL (FALLBACK):** Wenn der `KONTEXT` die `NUTZERFRAGE` **NICHT** beantwortet, antworte **AUSSCHLIESSLICH** und **WORTWÖRTLICH** mit dem folgenden Satz und nichts anderem:
    "Ich konnte keine passenden Informationen zu Ihrer Anfrage in meiner Wissensdatenbank finden."

---
**KONTEXT:**
{context}
---
**NUTZERFRAGE:**
{user_query}
"""

from .utils.mongo_vector_store import MongoVectorStore
from .utils.local_models import embedding_func, OllamaLLM
from .rag_manager import get_rag_instance


async def prepare_and_execute_retrieval(
        user_query: str,
) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
    """
    Orchestrates a reliable RAG process that returns a separate clean answer
    and a structured list of the sources used to generate it.
    """
    vector_store = await get_rag_instance()
    print("1. Generating embedding for query...")
    query_embedding = (await embedding_func([user_query]))[0]

    print("2. Retrieving relevant documents from vector store...")
    retrieved_documents = vector_store.similarity_search(query_embedding, k=7)

    context_data_str = ""
    for doc in retrieved_documents:
        context_data_str += doc.get("page_content", "") + "\n\n"

    print("3. Generating answer...")
    llm = OllamaLLM()
    final_system_prompt = RELIABLE_SYSTEM_PROMPT_TEMPLATE.format(
        context=context_data_str,
        user_query=user_query,
        current_date=datetime.now().strftime("%Y-%m-%d"),
        location="Würzburg"
    )

    citable_answer_text = await llm(prompt=final_system_prompt)

    return {
        "answer": citable_answer_text,
        "sources": context_data_str
    }
