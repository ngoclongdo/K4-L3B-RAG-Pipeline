"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re

from .task4_chunking_indexing import chunk_documents, load_documents


CORPUS: list[dict] = []


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Plus

    # ponytail: BM25Plus vì BM25Okapi cho IDF=0 khi corpus nhỏ (term xuất hiện ở N/2 docs)
    return BM25Plus([tokenize(item["content"]) for item in corpus])


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    query_tokens = tokenize(query)
    if top_k <= 0 or not query_tokens:
        return []
    if not CORPUS:
        CORPUS.extend(chunk_documents(load_documents()))
    if not CORPUS:
        return []

    # ponytail: build lại index mỗi query, O(N); cache khi corpus lớn
    scores = build_bm25_index(CORPUS).get_scores(query_tokens)
    query_set = set(query_tokens)
    ranked = sorted(
        (
            (float(score), item)
            for score, item in zip(scores, CORPUS)
            if query_set & set(tokenize(item["content"]))
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
