from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from app.services.scraper import scrape_content
from app.services.loader import load_pdf_content
from app.services.analyzer import analyze_content
from app.services.chunker import chunk_web_content, chunk_pdf_content
from app.services.storage import store_chunks


class GraphState(TypedDict):
    input_url: Optional[str] = None
    pdf_path: Optional[str] = None
    content: Optional[str] = None
    llm_output: Optional[str] = None
    chunks: Optional[List[Dict[str, Any]]] = None
    collection_name: Optional[str] = None
    storage_info: Optional[str] = None
    error: Optional[str] = None


def router(state: GraphState) -> str:
    input_url = state.get("input_url", "").strip()
    pdf_path = state.get("pdf_path", "").strip()

    if input_url and not pdf_path:
        return "scrape"
    elif pdf_path and not input_url:
        return "pdf_loader"
    elif input_url and pdf_path:
        return "scrape" 
    else:
        return "error"


def error_node(state: GraphState) -> Dict[str, Any]:
    return {"error": "Provide either input_url or pdf_path."}


def build_ingestion_graph() -> Any:
    graph_builder = StateGraph(GraphState)

    graph_builder.add_node("scrape", scrape_content)
    graph_builder.add_node("analyze", analyze_content)
    graph_builder.add_node(
        "chunk_web", lambda state: {"chunks": chunk_web_content(state["content"])}
    )
    graph_builder.add_node("store_web", store_chunks)

    graph_builder.add_node("pdf_loader", load_pdf_content)
    graph_builder.add_node(
        "chunk_pdf", lambda state: {"chunks": chunk_pdf_content(state["content"])}
    )
    graph_builder.add_node("store_pdf", store_chunks)

    graph_builder.add_node("error", error_node)

    graph_builder.add_conditional_edges(
        START,
        router,
        {"scrape": "scrape", "pdf_loader": "pdf_loader", "error": "error"},
    )

    graph_builder.add_edge("scrape", "analyze")
    graph_builder.add_edge("analyze", "chunk_web")
    graph_builder.add_edge("chunk_web", "store_web")
    graph_builder.add_edge("store_web", END)

    graph_builder.add_edge("pdf_loader", "chunk_pdf")
    graph_builder.add_edge("chunk_pdf", "store_pdf")
    graph_builder.add_edge("store_pdf", END)

    graph_builder.add_edge("error", END)

    return graph_builder.compile()  
