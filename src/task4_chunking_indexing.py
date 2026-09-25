"""
Task 4 — Chunking, embedding và indexing vào ChromaDB.
"""

import hashlib
import json
from pathlib import Path
from typing import Iterable

import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from src.contracts import Chunk, Document, EmbeddedChunk, validate_document


# ---- Cấu hình ----
BASE_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = BASE_DIR / "data" / "standardized"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
COLLECTION_NAME = "rag_corpus"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Cache model để không load lại nhiều lần
_MODEL: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(EMBEDDING_MODEL)
    return _MODEL


# ---- Load documents ----
def _stable_id(source: str, title: str) -> str:
    """Sinh id ổn định từ source + title để re-index không tạo bản trùng."""
    key = f"{source}::{title}".encode("utf-8")
    return hashlib.sha1(key).hexdigest()[:16]


def _read_markdown_files(root: Path, doc_type: str) -> Iterable[Document]:
    """Đọc mọi file .md dưới ``root`` và trả về Document theo contract."""
    if not root.exists():
        return

    for md_file in sorted(root.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        # Đọc metadata sidecar (nếu có), fallback là tên file
        meta_file = md_file.with_suffix(".json")
        url = None
        title = md_file.stem
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                title = meta.get("title") or title
                url = meta.get("url")
            except Exception:
                pass

        source = str(md_file.relative_to(BASE_DIR))
        doc: Document = {
            "id": _stable_id(source, title),
            "content": content,
            "metadata": {
                "source": source,
                "title": title,
                "doc_type": doc_type,
                "url": url,
            },
        }
        validate_document(doc)
        yield doc


def load_documents() -> list[Document]:
    """Load tất cả tài liệu chuẩn hóa từ data/standardized/{legal,news}."""
    documents: list[Document] = []
    documents.extend(_read_markdown_files(STANDARDIZED_DIR / "legal", "legal"))
    documents.extend(_read_markdown_files(STANDARDIZED_DIR / "news", "news"))
    print(f"Loaded {len(documents)} documents")
    return documents


# ---- Chunking ----
def chunk_documents(documents: list[Document]) -> list[Chunk]:
    """Chia mỗi document thành các Chunk theo contract."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks: list[Chunk] = []
    for doc in documents:
        parts = splitter.split_text(doc["content"])
        for idx, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            chunk: Chunk = {
                "id": f"{doc['id']}::chunk_{idx:04d}",
                "content": part,
                "metadata": {
                    **doc["metadata"],
                    "chunk_index": idx,
                },
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
    print(f"Created {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


# ---- Embedding ----
def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Điểm dùng chung: task 4 embed corpus, task 5 embed query.
    Đảm bảo cùng model + dimension.
    """
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=False,
    )
    return [v.tolist() for v in vectors]


def embed_chunks(chunks: list[Chunk]) -> list[EmbeddedChunk]:
    """Gắn embedding vào từng chunk."""
    vectors = embed_texts([c["content"] for c in chunks])
    return [
        {**chunk, "embedding": vec}
        for chunk, vec in zip(chunks, vectors)
    ]


# ---- Vector store ----
def get_collection() -> chromadb.Collection:
    """Trả về collection ChromaDB (persist local)."""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def index_to_vectorstore(embedded: list[EmbeddedChunk]) -> None:
    """Upsert chunk vào ChromaDB (idempotent theo id)."""
    if not embedded:
        print("Nothing to index.")
        return

    collection = get_collection()
    ids = [c["id"] for c in embedded]
    documents = [c["content"] for c in embedded]
    embeddings = [c["embedding"] for c in embedded]
    # ChromaDB không nhận None trong metadata -> replace bằng ""
    metadatas = [
        {k: (v if v is not None else "") for k, v in c["metadata"].items()}
        for c in embedded
    ]

    # upsert để re-index không nhân bản
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"Upserted {len(ids)} chunks. Collection size: {collection.count()}")


def main() -> None:
    documents = load_documents()
    if not documents:
        print("No documents found. Run Task 1-3 first.")
        return
    chunks = chunk_documents(documents)
    embedded = embed_chunks(chunks)
    index_to_vectorstore(embedded)


if __name__ == "__main__":
    main()