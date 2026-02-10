import uuid
import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.schemas import IngestUrlRequest, IngestResponse, AskRequest, AskResponse
from app.services.ingestion_graph import build_ingestion_graph
from app.services.qa import answer_question
from app.services.storage import client

router = APIRouter()


@router.post("/ingest/url", response_model=IngestResponse)
def ingest_url_endpoint(body: IngestUrlRequest):
    graph = build_ingestion_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke({"input_url": body.url, "pdf_path": ""}, config=config)

    return IngestResponse(
        collection_name=state.get("collection_name"),
        storage_info=state.get("storage_info"),
        llm_output=state.get("llm_output"),
        error=state.get("error"),
    )


@router.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf_endpoint(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(await file.read())
        pdf_path = tmp_file.name

    try:
        graph = build_ingestion_graph()
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        state = graph.invoke({"input_url": "", "pdf_path": pdf_path}, config=config)

        return IngestResponse(
            collection_name=state.get("collection_name"),
            storage_info=state.get("storage_info"),
            llm_output=state.get("llm_output"), 
            error=state.get("error"),
        )
    finally:
        os.unlink(pdf_path)


@router.post("/ask", response_model=AskResponse)
def ask_endpoint(body: AskRequest):
    if not client.collection_exists(body.collection_name):
        raise HTTPException(
            status_code=404, detail=f"Collection '{body.collection_name}' not found"
        )

    answer = answer_question(
        body.question, body.history or [], body.collection_name  
    )
    return AskResponse(answer=answer)
