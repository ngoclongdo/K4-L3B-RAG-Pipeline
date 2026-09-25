"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


import json
import logging
import time
from typing import Any

from pageindex import PageIndexClient

logger = logging.getLogger(__name__)

DOC_INDEX_CACHE_FILE = Path(__file__).parent.parent / "data" / "pageindex_cache.json"


def _get_client() -> PageIndexClient | None:
    if not PAGEINDEX_API_KEY:
        return None
    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


def load_cached_doc_ids() -> dict[str, str]:
    """Load cached mapping of source_file -> doc_id."""
    if DOC_INDEX_CACHE_FILE.exists():
        try:
            return json.loads(DOC_INDEX_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception as error:
            logger.warning("Failed to load pageindex cache: %s", error)
    return {}


def save_cached_doc_ids(cache: dict[str, str]) -> None:
    """Save mapping of source_file -> doc_id to cache file."""
    try:
        DOC_INDEX_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        DOC_INDEX_CACHE_FILE.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as error:
        logger.warning("Failed to save pageindex cache: %s", error)


def upload_documents() -> dict[str, str]:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    client = _get_client()
    if client is None:
        logger.warning("PAGEINDEX_API_KEY is not configured. Skipping upload.")
        return {}

    cache = load_cached_doc_ids()
    landing_legal_dir = Path(__file__).parent.parent / "data" / "landing" / "legal"
    files_to_upload: list[Path] = []

    # PageIndex accepts PDF directly
    if landing_legal_dir.is_dir():
        for p in landing_legal_dir.iterdir():
            if p.is_file() and p.suffix.lower() == ".pdf":
                files_to_upload.append(p)

    updated = False
    for file_path in files_to_upload:
        file_key = file_path.name
        if file_key in cache:
            continue
        try:
            response = client.submit_document(file_path=str(file_path))
            doc_id = response.get("doc_id")
            if doc_id:
                cache[file_key] = doc_id
                updated = True
                logger.info("Uploaded %s to PageIndex with doc_id=%s", file_key, doc_id)
        except Exception as error:
            logger.error("Failed to upload %s to PageIndex: %s", file_path.name, error)

    if updated:
        save_cached_doc_ids(cache)

    return cache


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult tuân thủ schema và không crash nếu lỗi."""
    client = _get_client()
    if client is None:
        return []

    cache = load_cached_doc_ids()
    if not cache:
        return []

    results: list[dict] = []

    for source_file, doc_id in cache.items():
        try:
            submit_resp = client.submit_query(doc_id=doc_id, query=query)
            retrieval_id = submit_resp.get("retrieval_id")
            if not retrieval_id:
                continue

            # Poll for retrieval results with short timeout (max 5s)
            retrieval_data: dict[str, Any] = {}
            for _ in range(5):
                status_resp = client.get_retrieval(retrieval_id=retrieval_id)
                status = status_resp.get("status")
                if status == "completed":
                    retrieval_data = status_resp
                    break
                if status in ("failed", "error"):
                    break
                time.sleep(1)

            nodes = retrieval_data.get("result", []) or retrieval_data.get("nodes", [])
            for idx, node in enumerate(nodes):
                content = node.get("content") or node.get("text") or ""
                if not content.strip():
                    continue

                raw_score = node.get("score")
                score = float(raw_score) if isinstance(raw_score, (int, float)) else 1.0 / (idx + 1)

                result_item = {
                    "id": f"pageindex-{doc_id}-{idx}",
                    "content": content.strip(),
                    "score": score,
                    "metadata": {
                        "source": source_file,
                        "title": source_file,
                        "doc_type": "legal",
                        "url": None,
                        "chunk_index": idx,
                    },
                    "retrieval_method": "pageindex",
                }
                results.append(result_item)
        except Exception as error:
            logger.warning("PageIndex search failed on doc_id %s: %s", doc_id, error)
            continue

    # Sắp xếp giảm dần theo điểm số
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    upload_documents()

