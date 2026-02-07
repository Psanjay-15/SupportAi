import re
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_ollama import ChatOllama
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from app.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    LLM_MODEL,
    LLM_TEMPERATURE,
    EMBEDDING_MODEL,
)
# from app.services.notifier import send_push_notification, 
from app.services.notifier import send_email_notification
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"}
)
llm = ChatOllama(model=LLM_MODEL, temperature=0.2)
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
RETRIEVAL_K = 5
NO_ANSWER_MESSAGE = "No answer found our team will reach out to you."

SYSTEM_PROMPT = """
You are a strict retrieval-based question answering system for a website.

Your task is to answer the user's question using ONLY the information explicitly stated in the provided context.
The context contains text extracted from the website such as policies, documentation, or FAQ content.

Strict rules you MUST follow:
1. Use ONLY the provided context to generate your answer.
2. The answer MUST be explicitly stated in the context. Do NOT infer, assume, summarize beyond the text, or combine unrelated statements.
3. Do NOT use any external knowledge or general understanding.
4. Do NOT add explanations, opinions, or extra details not present in the context.
5. Do NOT mention the context, documents, chunks, or sources in your response.
6. Keep the answer clear, concise, and factual.
7. If multiple sentences in the context directly answer the question, combine them without changing their meaning.

If the context does NOT explicitly contain the answer, respond EXACTLY with:
"No answer found our team will reach out to you."

Context:
{context}
"""


def rewrite_query(question: str, history: List[Dict[str, str]]) -> str:
    formatted_history = "\n".join(
        (
            f"User: {item['content']}"
            if item["role"] == "user"
            else f"Assistant: {item['content']}"
        )
        for item in history
    )

    system_prompt = """
You are a query rewriting agent for an enterprise knowledge base.

Your task is to rewrite the user's latest question into a short, clear, and precise
search query that will retrieve the most relevant information from official company documents.

Rules:
1. Use ONLY the user's question and the conversation history.
2. Preserve the user's original intent exactly.
3. Remove conversational words, filler, and ambiguity.
4. Include important entities, features, policies, or actions mentioned by the user.
5. Do NOT answer the question.
6. Do NOT add new information or assumptions.
7. Do NOT use external knowledge.
8. Output ONLY the rewritten query as a single sentence.

If the user question is already clear and suitable for search, return it unchanged.
"""

    user_prompt = f"""
Conversation history:
{formatted_history}

User question:
{question}

Rewritten query:
"""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

    response = llm.invoke(messages)
    rewritten_query = response.content.strip()
    return rewritten_query


def rerank_chunks(question: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    system_prompt = """
You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk, nothing else. Include all the chunk ids you are provided with, reranked.
"""

    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks, start=1):
        user_prompt += f"# CHUNK ID: {index}\n\n{chunk['content']}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

    response = llm.invoke(messages)
    data = response.content.strip()
    # print("reranker response:", data)  

    matches = re.findall(r"(?:#\s*)?CHUNK\s+ID[:\s-]*(\d+)", data, flags=re.IGNORECASE)
    if not matches:
        matches = re.findall(r"\b(\d+)\b", data)

    ranked_ids = []
    for raw_id in matches:
        idx = int(raw_id)
        if 1 <= idx <= len(chunks) and idx not in ranked_ids:
            ranked_ids.append(idx)

    if not ranked_ids:
        # print("Unable to parse reranker ids; falling back to original order.") 
        return chunks

    remaining = [i for i in range(1, len(chunks) + 1) if i not in ranked_ids]
    ranked_ids.extend(remaining)

    return [chunks[i - 1] for i in ranked_ids]


def fetch_context_unranked(question: str, collection_name: str) -> List[Dict[str, Any]]:
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    retriever = vectorstore.as_retriever()
    documents = retriever.invoke(question)
    # print(documents)      
    # print(len(documents))  
    chunks = []
    for doc in documents[:RETRIEVAL_K]:
        chunks.append({"content": doc.page_content, "metadata": doc.metadata})
    return chunks


def fetch_context(question: str, collection_name: str) -> List[Dict[str, Any]]:
    chunks = fetch_context_unranked(question, collection_name)
    # print("chunks", chunks)  
    return rerank_chunks(question, chunks)


def make_rag_messages(
    question: str, history: List[Dict[str, str]], chunks: List[Dict[str, Any]]
) -> List[BaseMessage]:
    context = "\n\n".join(
        f"Extract from {chunk['metadata'].get('_collection_name', 'unknown')} (ID: {chunk['metadata'].get('_id', 'unknown')}):\n{chunk['content']}"
        for chunk in chunks
    )

    system_prompt = SYSTEM_PROMPT.format(context=context)

    dict_messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )

    messages = []
    for m in dict_messages:
        if m["role"] == "system":
            messages.append(SystemMessage(content=m["content"]))
        elif m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            messages.append(AIMessage(content=m["content"]))

    return messages


def answer_question(
    question: str, history: List[Dict[str, str]], collection_name: str
) -> str:
    rewritten_query = rewrite_query(question, history)
    # print("Rewritten query:", rewritten_query)  

    chunks = fetch_context(rewritten_query, collection_name)

    if not chunks:
        # send_push_notification(question)
        send_email_notification(question, "No relevant chunks found")
        return NO_ANSWER_MESSAGE

    messages = make_rag_messages(question, history, chunks)

    response = llm.invoke(messages)

    answer = response.content.strip()

    if answer == NO_ANSWER_MESSAGE:
        send_email_notification(question)

    return answer
