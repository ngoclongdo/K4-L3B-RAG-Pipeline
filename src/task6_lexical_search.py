"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re

from .task4_chunking_indexing import chunk_documents, load_documents


CORPUS: list[dict] = []
_INDEX_CACHE: dict = {}


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Plus

    # ponytail: BM25Plus vì BM25Okapi cho IDF=0 khi corpus nhỏ (term xuất hiện ở N/2 docs)
    return BM25Plus([tokenize(item["content"]) for item in corpus])


def get_index():
    """Build BM25 index một lần cho mỗi corpus; build lại khi CORPUS bị thay hoặc đổi kích thước."""
    key = (id(CORPUS), len(CORPUS))
    if _INDEX_CACHE.get("key") != key:
        _INDEX_CACHE.update(
            key=key,
            bm25=build_bm25_index(CORPUS),
            token_sets=[set(tokenize(item["content"])) for item in CORPUS],
        )
    return _INDEX_CACHE["bm25"], _INDEX_CACHE["token_sets"]


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    query_tokens = tokenize(query)
    if top_k <= 0 or not query_tokens:
        return []
    if not CORPUS:
        CORPUS.extend(chunk_documents(load_documents()))
    if not CORPUS:
        return []

    bm25, token_sets = get_index()
    scores = bm25.get_scores(query_tokens)
    query_set = set(query_tokens)
    ranked = sorted(
        (
            (float(score), item)
            for score, item, tokens in zip(scores, CORPUS, token_sets)
            if query_set & tokens
        ),
        key=lambda pair: pair[0],
        reverse=True,
    )
    return [
        {
            "id": item["id"],
            "content": item["content"],
            "score": score,
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        }
        for score, item in ranked[:top_k]
    ]


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
