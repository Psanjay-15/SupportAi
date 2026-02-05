import logging
from fastapi import FastAPI
from app.routers import api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SupportAi",
    description="A retrieval-augmented generation system for web/PDF ingestion and question answering.",
    version="1.0.0",
)

app.include_router(api.router, prefix="/api/v1")
