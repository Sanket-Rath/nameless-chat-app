import os
import json
import faiss
import numpy as np
import google.generativeai as genai
from pypdf import PdfReader

from backend.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_DIR = os.path.join(BASE_DIR, "vector_store")
os.makedirs(VECTOR_DIR, exist_ok=True)

EMBED_MODEL = "models/gemini-embedding-001"
CHAT_MODEL = "gemini-2.5-flash"
CHUNK_SIZE = 600
TOP_K = 4

chat_model = genai.GenerativeModel(
    CHAT_MODEL,
    system_instruction="You answer questions based only on the provided document context. If the answer isn't in the context, say you couldn't find it in the uploaded file.",
)


def _doc_store_path(doc_id: int):
    folder = os.path.join(VECTOR_DIR, f"doc_{doc_id}")
    os.makedirs(folder, exist_ok=True)
    return folder


def extract_text(file_path: str) -> str:
    ext = file_path.lower().split(".")[-1]

    if ext == "pdf":
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)

    if ext in ("txt", "md", "csv"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    raise ValueError(f"Unsupported file type: .{ext}")


def chunk_text(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - 80  # bit of overlap

    return chunks


def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:
    try:
        result = genai.embed_content(
            model=EMBED_MODEL,
            content=text,
            task_type=task_type,
        )
        return result["embedding"]
    except Exception as e:
        raise RuntimeError(f"Embedding failed: {e}") from e


def build_index(doc_id: int, chunks: list[str]):
    if not chunks:
        return False

    embeddings = []
    for chunk in chunks:
        emb = embed_text(chunk, task_type="retrieval_document")
        embeddings.append(emb)

    vectors = np.array(embeddings, dtype="float32")
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    folder = _doc_store_path(doc_id)
    faiss.write_index(index, os.path.join(folder, "index.faiss"))

    with open(os.path.join(folder, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f)

    return True


def process_document(doc_id: int, file_path: str) -> dict:
    text = extract_text(file_path)
    chunks = chunk_text(text)

    if not chunks:
        return {"indexed": False, "chunks": 0, "message": "No readable text found in file"}

    ok = build_index(doc_id, chunks)
    return {
        "indexed": ok,
        "chunks": len(chunks),
        "message": f"Indexed {len(chunks)} chunks from document",
    }


def _search_doc(doc_id: int, query_vec: np.ndarray, k: int = TOP_K) -> list[str]:
    folder = _doc_store_path(doc_id)
    index_path = os.path.join(folder, "index.faiss")
    chunks_path = os.path.join(folder, "chunks.json")

    if not os.path.exists(index_path):
        return []

    index = faiss.read_index(index_path)
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    scores, ids = index.search(query_vec, min(k, len(chunks)))
    results = []
    for idx in ids[0]:
        if idx >= 0 and idx < len(chunks):
            results.append(chunks[idx])

    return results


def ask_with_rag(doc_ids: list[int], question: str) -> str:
    if not doc_ids:
        return "No documents uploaded yet."

    try:
        query_emb = embed_text(question, task_type="retrieval_query")
    except Exception as e:
        return f"Sorry, could not process your question: {e}"
    query_vec = np.array([query_emb], dtype="float32")
    faiss.normalize_L2(query_vec)

    all_chunks = []
    for doc_id in doc_ids:
        hits = _search_doc(doc_id, query_vec)
        all_chunks.extend(hits)

    if not all_chunks:
        return "I couldn't find relevant content in the uploaded file. Try re-uploading or ask something else."

    # dedupe while keeping order
    seen = set()
    unique_chunks = []
    for c in all_chunks:
        if c not in seen:
            seen.add(c)
            unique_chunks.append(c)

    context = "\n\n---\n\n".join(unique_chunks[:TOP_K])

    prompt = f"""Use the following document excerpts to answer the question.

Context:
{context}

Question: {question}

Answer:"""

    try:
        response = chat_model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=1000,
                temperature=0.3,
            ),
        )
        return response.text.strip()
    except Exception as e:
        return f"RAG error: {str(e)}"
