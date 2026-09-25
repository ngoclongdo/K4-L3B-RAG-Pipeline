"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk tuân theo docs/MODULE_CONTRACTS.md:

    - Document.id = đường dẫn tương đối của file .md (vd "news/article_01.md")
      nên ổn định giữa các lần chạy; chunk id = "<doc_id>::chunk-<index>".
    - metadata.source/title/doc_type/url giữ nguyên từ document sang mọi chunk.
      Với news, title và url được parse ngược từ header Markdown mà Task 3 ghi.
    - Upsert theo id ổn định => chạy lại KHÔNG nhân bản dữ liệu trong Chroma.
    - embed_texts() là entrypoint duy nhất; Task 5 import lại chính hàm này để
      query embedding luôn cùng model/dimension với corpus embedding.

Cấu hình qua .env (xem .env.example):
    EMBEDDING_PROVIDER = sentence_transformers | openai | gemini
    EMBEDDING_MODEL    = tên model tương ứng provider (mặc định BAAI/bge-m3)

Lựa chọn tham số của nhóm (giải thích trong báo cáo):
    CHUNK_SIZE = 500 ký tự: vừa đủ giữ một "Điều" luật hoặc 2-3 đoạn tin tức,
    định vị chính xác hơn chunk 1000 nhưng chưa tách mất ngữ cảnh.
    CHUNK_OVERLAP = 50 (10%): giữ liền mạch câu cuối/đầu giữa hai chunk kề nhau
    với chi phí embedding tăng không đáng kể.
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").strip().lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3").strip()
EMBEDDING_DIM = 1024  # BAAI/bge-m3; đổi model thì cập nhật lại để ghi vào báo cáo

COLLECTION_NAME = "rag_documents"

# Batch sizes: giới hạn request của API embedding và của Chroma upsert.
EMBED_BATCH_SIZE = 64
UPSERT_BATCH_SIZE = 500

# Cache model local để embed_texts() gọi nhiều lần không load lại model.
_ST_MODEL = None
_ST_MODEL_NAME = None


# ---------------------------------------------------------------------------
# Embedding — entrypoint dùng chung cho Task 4 (corpus) và Task 5 (query)
# ---------------------------------------------------------------------------

def _embed_sentence_transformers(texts: list[str]) -> list[list[float]]:
    """Embed bằng model local (mặc định BAAI/bge-m3, 1024 dims)."""
    global _ST_MODEL, _ST_MODEL_NAME
    from sentence_transformers import SentenceTransformer

    if _ST_MODEL is None or _ST_MODEL_NAME != EMBEDDING_MODEL:
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        _ST_MODEL = SentenceTransformer(EMBEDDING_MODEL)
        _ST_MODEL_NAME = EMBEDDING_MODEL

    vectors = _ST_MODEL.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,  # chuẩn hóa L2 cho cosine similarity ổn định
        show_progress_bar=len(texts) > 100,
    )
    return vectors.tolist()


def _embed_openai(texts: list[str]) -> list[list[float]]:
    """Embed bằng OpenAI; cần OPENAI_API_KEY trong .env."""
    from openai import OpenAI

    client = OpenAI()  # tự đọc OPENAI_API_KEY từ môi trường
    vectors: list[list[float]] = []
    for start in range(0, len(texts), 100):  # giới hạn input mỗi request
        batch = texts[start:start + 100]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        vectors.extend(item.embedding for item in response.data)
    return vectors


def _embed_gemini(texts: list[str]) -> list[list[float]]:
    """Embed bằng Gemini; cần GEMINI_API_KEY trong .env."""
    from google import genai

    client = genai.Client()  # tự đọc GEMINI_API_KEY từ môi trường
    vectors: list[list[float]] = []
    for start in range(0, len(texts), 100):
        batch = texts[start:start + 100]
        response = client.models.embed_content(model=EMBEDDING_MODEL, contents=batch)
        vectors.extend(list(embedding.values) for embedding in response.embeddings)
    return vectors


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed một danh sách văn bản, dispatch theo EMBEDDING_PROVIDER.

    Task 5 phải gọi lại đúng hàm này để query cùng model/dimension với corpus.
    """
    # Một số provider từ chối chuỗi rỗng; chunk rỗng đã bị loại ở chunk_documents
    # nhưng embed_texts() cũng được Task 5 gọi trực tiếp với query tự do.
    cleaned = [text if text.strip() else " " for text in texts]
    if not cleaned:
        return []

    if EMBEDDING_PROVIDER == "sentence_transformers":
        return _embed_sentence_transformers(cleaned)
    if EMBEDDING_PROVIDER == "openai":
        return _embed_openai(cleaned)
    if EMBEDDING_PROVIDER == "gemini":
        return _embed_gemini(cleaned)
    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER!r} "
        "(expected: sentence_transformers | openai | gemini)"
    )


# ---------------------------------------------------------------------------
# ChromaDB collection — cosine distance, persistent trên đĩa
# ---------------------------------------------------------------------------

def get_collection():
    """Mở Chroma collection dùng cosine distance (tạo mới nếu chưa có)."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Load documents — Document theo contract, id ổn định theo đường dẫn file
# ---------------------------------------------------------------------------

def _parse_news_header(content: str) -> dict:
    """Trích title/url từ header Markdown mà Task 3 ghi cho bài viết news.

    Header dạng:
        # <title>
        **Source:** <url>
        **Crawled:** <iso date>
    """
    title_match = re.search(r"^#\s+(.+?)\s*$", content, flags=re.MULTILINE)
    url_match = re.search(r"^\*\*Source:\*\*\s*(\S+)\s*$", content, flags=re.MULTILINE)
    return {
        "title": title_match.group(1) if title_match else None,
        "url": url_match.group(1) if url_match else None,
    }


def load_documents() -> list[dict]:
    """Đọc mọi Markdown trong data/standardized và trả về list[Document]."""
    documents = []

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            print(f"Skipped (empty file): {path.name}")
            continue

        doc_type = "legal" if "legal" in path.parts else "news"
        header = _parse_news_header(content) if doc_type == "news" else {}

        documents.append({
            # id ổn định: chỉ phụ thuộc vị trí file, không phụ thuộc lần chạy.
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": {
                "source": path.name,
                "title": header.get("title") or path.stem.replace("-", " "),
                "doc_type": doc_type,
                "url": header.get("url"),
            },
        })

    print(f"Loaded {len(documents)} documents from {STANDARDIZED_DIR}")
    return documents


# ---------------------------------------------------------------------------
# Chunking — recursive character splitting, giữ quan hệ chunk <-> document
# ---------------------------------------------------------------------------

def _get_text_splitter():
    """Splitter duy nhất của pipeline; đổi tham số thì sửa ở đây."""
    if CHUNKING_METHOD != "recursive":
        raise ValueError(f"Unsupported CHUNKING_METHOD: {CHUNKING_METHOD!r}")

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id duy nhất và metadata.chunk_index.

    - chunk["id"] = "<document_id>::chunk-<index>"
    - chunk["metadata"] = copy của document metadata + chunk_index (không mutate
      document gốc)
    - chunk rỗng sau khi strip bị loại để thỏa contract "content không rỗng"
    """
    if not documents:
        return []

    splitter = _get_text_splitter()
    chunks = []

    for document in documents:
        pieces = splitter.split_text(document["content"])
        for index, text in enumerate(pieces):
            text = text.strip()
            if not text:
                continue
            chunks.append({
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {**document["metadata"], "chunk_index": index},
            })

    return chunks


# ---------------------------------------------------------------------------
# Embed + index — upsert theo id ổn định nên chạy lại không trùng dữ liệu
# ---------------------------------------------------------------------------

def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Gắn trường "embedding" vào từng chunk, giữ nguyên các field còn lại."""
    if not chunks:
        return chunks

    total = len(chunks)
    for start in range(0, total, EMBED_BATCH_SIZE):
        batch = chunks[start:start + EMBED_BATCH_SIZE]
        vectors = embed_texts([chunk["content"] for chunk in batch])
        for chunk, vector in zip(batch, vectors):
            chunk["embedding"] = vector
        print(f"Embedded {min(start + EMBED_BATCH_SIZE, total)}/{total} chunks")

    return chunks


def _sanitize_metadata(metadata: dict) -> dict:
    """Chroma không nhận None trong metadata ở một số phiên bản -> đổi thành "".

    Contract vẫn thỏa mãn vì validate chấp nhận url là str (kể cả rỗng) hoặc None.
    """
    return {key: ("" if value is None else value) for key, value in metadata.items()}


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert ids/documents/embeddings/metadatas vào ChromaDB theo batch."""
    if not chunks:
        print("No chunks to index.")
        return

    collection = get_collection()

    for start in range(0, len(chunks), UPSERT_BATCH_SIZE):
        batch = chunks[start:start + UPSERT_BATCH_SIZE]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[_sanitize_metadata(chunk["metadata"]) for chunk in batch],
        )

    print(f"Upserted {len(chunks)} chunks into collection {COLLECTION_NAME!r}")


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline() -> None:
    """Chạy load -> chunk -> embed -> index và in thống kê cho báo cáo."""
    documents = load_documents()
    chunks = chunk_documents(documents)

    if not chunks:
        print("No chunks produced. Run task1-3 trước để có data/standardized.")
        return

    lengths = [len(chunk["content"]) for chunk in chunks]
    print(
        f"Chunks: {len(chunks)} | size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP} "
        f"| len min/avg/max: {min(lengths)}/{sum(lengths) // len(lengths)}/{max(lengths)}"
    )

    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)

    count = get_collection().count()
    print(f"Indexed {len(embedded_chunks)} chunks | collection total: {count}")
    if count > len(embedded_chunks):
        print(
            "NOTE: collection có nhiều hơn số chunk hiện tại — có thể corpus đã đổi. "
            "Chunk cũ của file đã xóa sẽ còn sót lại; cân nhắc xóa chroma_db/ rồi "
            "index lại nếu corpus thay đổi lớn."
        )


if __name__ == "__main__":
    run_pipeline()