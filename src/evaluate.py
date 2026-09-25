"""
Evaluation — 4 metric và A/B dense-only vs hybrid + RRF.

Metric theo định nghĩa RAGAS nhưng chấm deterministic (token overlap + embedding),
không cần evaluator LLM nên chạy lại được và không tốn API:
    - context_recall: tỷ lệ câu trong expected_context được một chunk retrieve phủ >= 70% token.
    - context_precision: average precision theo rank; chunk relevant khi phủ >= 50% token của một câu expected.
    - faithfulness: tỷ lệ câu trong answer có >= 60% token nằm trong context đã retrieve.
    - answer_relevance: cosine(embedding(question), embedding(answer)) bằng embedding model của Task 4.
Thêm source_mrr (1/rank của chunk đầu tiên thuộc expected_source) làm chỉ số chẩn đoán retrieval.

Chạy: python -m src.evaluate
"""

import json
import re
import statistics
import time
from pathlib import Path

from .task4_chunking_indexing import embed_texts
from .task6_lexical_search import tokenize
from .task9_retrieval_pipeline import SCORE_THRESHOLD, retrieve
from .task10_generation import REFUSAL, generate_from_chunks


ROOT = Path(__file__).parent.parent
EVALUATION_DIR = ROOT / "group_project" / "evaluation"
TOP_K = 5
METRICS = ("faithfulness", "answer_relevance", "context_recall", "context_precision")
CONFIGS = {"A_dense_only": False, "B_hybrid_rrf": True}
STOPWORDS = {
    "và", "của", "có", "là", "cho", "các", "được", "không", "thì", "theo", "với", "trong", "này",
    "đã", "khi", "những", "một", "để", "từ", "tại", "hoặc", "bao", "nhiêu", "nào", "gì", "ai",
}
RECALL_COVERAGE = 0.7
RELEVANT_COVERAGE = 0.5
SUPPORTED_COVERAGE = 0.6


def content_tokens(text: str) -> set[str]:
    return {token for token in tokenize(text) if token not in STOPWORDS}


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.;!?])\s+|\n+", re.sub(r"\[\d+\]", "", text))
    return [part for part in parts if len(content_tokens(part)) >= 3]


def coverage(needle: set[str], haystack: set[str]) -> float:
    return len(needle & haystack) / len(needle) if needle else 0.0


def context_recall(expected_context: str, chunks: list[dict]) -> float:
    targets = [content_tokens(s) for s in sentences(expected_context)] or [content_tokens(expected_context)]
    chunk_tokens = [content_tokens(chunk["content"]) for chunk in chunks]
    hit = sum(any(coverage(t, c) >= RECALL_COVERAGE for c in chunk_tokens) for t in targets)
    return hit / len(targets)


def context_precision(expected_context: str, chunks: list[dict]) -> float:
    targets = [content_tokens(s) for s in sentences(expected_context)] or [content_tokens(expected_context)]
    relevant = [
        any(coverage(t, content_tokens(chunk["content"])) >= RELEVANT_COVERAGE for t in targets)
        for chunk in chunks
    ]
    precisions = [sum(relevant[: rank + 1]) / (rank + 1) for rank, rel in enumerate(relevant) if rel]
    return sum(precisions) / len(precisions) if precisions else 0.0


def faithfulness(answer: str, chunks: list[dict]) -> float | None:
    claims = sentences(answer)
    if not claims or answer.strip() == REFUSAL:
        return None
    context = set().union(*(content_tokens(chunk["content"]) for chunk in chunks)) if chunks else set()
    return sum(coverage(content_tokens(c), context) >= SUPPORTED_COVERAGE for c in claims) / len(claims)


def answer_relevance(question: str, answer: str) -> float:
    question_vector, answer_vector = embed_texts([question, answer])
    return max(0.0, sum(q * a for q, a in zip(question_vector, answer_vector)))


def source_mrr(expected_source: str | None, chunks: list[dict]) -> float:
    for rank, chunk in enumerate(chunks, 1):
        if expected_source and expected_source.endswith(chunk["metadata"]["source"]):
            return 1 / rank
    return 0.0


def mean(values: list) -> float | None:
    values = [value for value in values if value is not None]
    return statistics.fmean(values) if values else None


def evaluate_config(dataset: list[dict], use_reranking: bool) -> dict:
    rows = []
    retrieval_seconds = generation_seconds = 0.0
    for case in dataset:
        started = time.perf_counter()
        chunks = retrieve(case["question"], top_k=TOP_K, use_reranking=use_reranking)
        retrieved = time.perf_counter()
        result = generate_from_chunks(case["question"], chunks)
        retrieval_seconds += retrieved - started
        generation_seconds += time.perf_counter() - retrieved
        scores = {
            "faithfulness": faithfulness(result["answer"], chunks),
            "answer_relevance": answer_relevance(case["question"], result["answer"]),
            "context_recall": context_recall(case["expected_context"], chunks),
            "context_precision": context_precision(case["expected_context"], chunks),
        }
        rows.append({
            "id": case["id"],
            "question": case["question"],
            "answer": result["answer"],
            "refused": result["answer"].strip() == REFUSAL,
            "error": result.get("error"),
            "expected_source": case.get("expected_source"),
            "retrieved_sources": [chunk["metadata"]["source"] for chunk in chunks],
            **scores,
            "average": mean(list(scores.values())),
            "source_mrr": source_mrr(case.get("expected_source"), chunks),
        })
    summary = {metric: mean([row[metric] for row in rows]) for metric in METRICS}
    summary["average"] = mean(list(summary.values()))
    summary["source_mrr"] = mean([row["source_mrr"] for row in rows])
    summary["refusal_rate"] = sum(row["refused"] for row in rows) / len(rows)
    summary["retrieval_seconds_per_query"] = retrieval_seconds / len(rows)
    summary["generation_seconds_per_query"] = generation_seconds / len(rows)
    return {"summary": summary, "rows": rows}


def fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def main() -> None:
    dataset = json.loads((EVALUATION_DIR / "golden_dataset.json").read_text(encoding="utf-8"))
    retrieve(dataset[0]["question"], top_k=TOP_K)  # warm up model/BM25 để latency so sánh công bằng
    results = {name: evaluate_config(dataset, flag) for name, flag in CONFIGS.items()}
    results["meta"] = {"top_k": TOP_K, "score_threshold": SCORE_THRESHOLD, "dataset_size": len(dataset)}
    output = EVALUATION_DIR / "eval_results.json"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    a, b = results["A_dense_only"]["summary"], results["B_hybrid_rrf"]["summary"]
    print("| Metric | Config A | Config B | Delta B−A |\n|---|---:|---:|---:|")
    for metric in (*METRICS, "average", "source_mrr", "refusal_rate", "retrieval_seconds_per_query", "generation_seconds_per_query"):
        delta = None if a[metric] is None or b[metric] is None else b[metric] - a[metric]
        print(f"| {metric} | {fmt(a[metric])} | {fmt(b[metric])} | {fmt(delta)} |")
    print(f"\nSaved: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
