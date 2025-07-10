from typing import List

from langchain.docstore.document import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


def create_structured_chunks(documents: List[Document]) -> List[Document]:
    """
    Nimmt eine Liste von LangChain-Dokumenten und teilt sie in strukturierte Chunks auf.
    - Nutzt MarkdownHeaderTextSplitter für HTML/Markdown-Inhalte.
    - Nutzt einen Fallback-Splitter für reine Text-Inhalte (z.B. aus PDFs).
    """
    final_chunks = []

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, strip_headers=False
    )

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for doc in documents:
        if doc.metadata.get("type") == "html":
            chunks = markdown_splitter.split_text(doc.page_content)
            for chunk in chunks:
                chunk.metadata.update(doc.metadata)
                final_chunks.append(chunk)
        else:
            chunks = text_splitter.split_documents([doc])
            final_chunks.extend(chunks)

    return final_chunks
