from typing import Dict, Any, List
from urllib.parse import urlparse
import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from app.config import QDRANT_HOST, QDRANT_PORT
from app.services.chunker import chunk_web_content  
from app.config import EMBEDDING_MODEL
from langchain_huggingface import HuggingFaceEmbeddings

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"}
)


def get_collection_name(input_url: str = "", pdf_path: str = "") -> str:
    if input_url:
        parsed = urlparse(input_url)
        domain = parsed.netloc.replace(".", "_").replace("-", "_")
        name = f"{domain}"
        return name.lower()

    elif pdf_path:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        pdf_name = pdf_name.replace(" ", "_").replace("-", "_").lower()[:50]
        return f"pdf_name"

    else:
        return "debug_unknown_source"


def store_chunks(state: Dict[str, Any]) -> Dict[str, Any]:
    chunks = state.get("chunks", [])
    if not chunks:
        # print("[store_node] No chunks found → skipping storage")  
        return {"storage_info": "No chunks to store"}

    # print(f"[store_node] Found {len(chunks)} chunks")  

    input_url = state.get("input_url", "").strip()
    pdf_path = state.get("pdf_path", "").strip()

    collection_name = get_collection_name(input_url=input_url, pdf_path=pdf_path)
    # print(f"[store_node] Using collection name: {collection_name}")  

    documents = [
        Document(page_content=chunk["content"], metadata=chunk.get("metadata", {}))
        for chunk in chunks
    ]

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        # print(f"[store_node] Created collection '{collection_name}'")

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    vectorstore.add_documents(documents)

    # print("[store_node] Documents added successfully")

    return {
        "collection_name": collection_name,
        "storage_info": f"Stored {len(documents)} vectors in '{collection_name}'",
    }
