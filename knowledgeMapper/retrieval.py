# In retrieval.py

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Set, Union

import config
from rag_manager import get_rag_instance
from utils.local_models import OllamaLLM, embedding_func

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RELIANCE_THRESHOLD = 0.85

RELIABLE_SYSTEM_PROMPT_TEMPLATE = """
Du bist ein hilfreicher Assistent der Hochschule THWS.
Beantworte die folgende Frage basierend auf dem gegebenen Kontext.
Antworte ausschließlich auf Deutsch und fasse dich klar und präzise.
Wenn du die Antwort im Kontext nicht finden kannst, sage "Ich weiß es leider nicht."

Kontext:
{context}

Frage:
{query}

Antwort:
"""

def extract_year_from_document(doc: Dict[str, Any]) -> int:
    """
    Tries to extract the most reliable publication year from a document's metadata.
    It prioritizes a dedicated 'publication_date' field, then looks for a year in the URL.
    """
    metadata = doc.get("metadata", {})
    
    # Priority 1: Check for a specific date field in metadata
    if pub_date_str := metadata.get("publication_date"):
        try:
            return datetime.fromisoformat(pub_date_str).year
        except (ValueError, TypeError):
            pass # Continue if parsing fails

    # Priority 2: Look for a 4-digit year (e.g., 2023) in the URL
    if url := metadata.get("url"):
        # This regex finds the latest year between 2000 and the current year
        current_year = datetime.now().year
        matches = re.findall(r'(20[0-2][0-9])', url)
        if matches:
            # Return the most recent year found in the URL
            return max(int(year) for year in matches if int(year) <= current_year)
            
    # Fallback: Return a very old year so it gets sorted last
    return 1970


async def get_rag_response(
    user_query: str,
    k: int = 15, # We retrieve more documents initially to have a better pool for re-ranking
    llm: OllamaLLM = None
) -> Dict[str, Union[str, List[str]]]:

    if not llm:
        llm = OllamaLLM()

    try:
        logging.info("Generating embedding for query...")
        query_embedding = (await embedding_func([user_query]))[0]

        logging.info(f"Retrieving up to {k} documents for initial ranking...")
        vector_store = await get_rag_instance()
        retrieved_documents = await vector_store.similarity_search(query_embedding, k=k)

        if not retrieved_documents:
            logging.warning("No documents found for the query.")
            return {"answer": "Ich weiß es leider nicht.", "sources": []}

        # --- MODIFIED LOGIC: Re-rank by relevance and then by date ---
        # 1. Filter documents by relevance score
        top_score = retrieved_documents[0].get("score", 0)
        min_score_threshold = top_score * RELIANCE_THRESHOLD
        
        relevant_docs = [
            doc for doc in retrieved_documents if doc.get("score", 0) >= min_score_threshold
        ]
        logging.info(f"Found {len(relevant_docs)} documents meeting the relevance threshold ({min_score_threshold:.2f}).")

        # 2. Add the publication year to each document and sort by year (newest first)
        for doc in relevant_docs:
            doc['year'] = extract_year_from_document(doc)
            
        # Sort primarily by year (descending), and secondarily by score (descending)
        # This ensures the most recent, highly relevant documents are prioritized.
        sorted_docs = sorted(relevant_docs, key=lambda d: (d['year'], d.get('score', 0)), reverse=True)
        
        # 3. Select the top 7 documents after re-ranking
        final_docs = sorted_docs[:7]
        # --- END OF MODIFIED LOGIC ---

        # 4. Build context and source links from the final, re-ranked documents
        context_parts = []
        unique_urls: Set[str] = set()

        for doc in final_docs:
            page_content = doc.get("page_content", "")
            context_parts.append(page_content)
            
            if metadata := doc.get("metadata"):
                if url := metadata.get("url"):
                    unique_urls.add(url)
        
        context_str = "\n\n---\n\n".join(context_parts)
        source_links = sorted(list(unique_urls))
        logging.info(f"Using {len(source_links)} unique and most up-to-date sources for context.")

        # 5. Generate the final answer
        logging.info("Generating answer...")
        final_prompt = RELIABLE_SYSTEM_PROMPT_TEMPLATE.format(
            context=context_str,
            query=user_query,
        )
        answer_text = await llm(prompt=final_prompt)

        return {"answer": answer_text.strip(), "sources": source_links}

    except Exception as e:
        logging.error(f"An error occurred in the RAG pipeline: {e}", exc_info=True)
        return {
            "answer": "Es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.",
            "sources": []
        }