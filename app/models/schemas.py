from typing import List, Dict, Optional
from pydantic import BaseModel


class IngestUrlRequest(BaseModel):
    url: str


class IngestResponse(BaseModel):
    collection_name: str
    storage_info: Optional[str]
    llm_output: Optional[str]  
    error: Optional[str]


class AskRequest(BaseModel):
    question: str
    collection_name: Optional[str] = "pdf_document"
    history: Optional[List[Dict[str, str]]] = (
        []
    )  


class AskResponse(BaseModel):
    answer: str
