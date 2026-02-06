from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_web_content(content: str) -> List[Dict[str, Any]]:
    if not content.strip():
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(content)
    # print(chunks) 
    return [{"content": c} for c in chunks]


def chunk_pdf_content(content: str) -> List[Dict[str, Any]]:
    if not content.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = splitter.split_text(content)
    return [{"content": chunk, "metadata": {"source": "pdf_chunk"}} for chunk in chunks]
