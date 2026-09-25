"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import logging
import os
import re

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()
logger = logging.getLogger(__name__)

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3
MAX_TOKENS = 1024

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-haiku-4-5-20251001",
}

REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
SYSTEM_PROMPT = f"""Bạn là trợ lý tra cứu quy định về hộ kinh doanh, đăng ký doanh nghiệp và thuế tại Việt Nam.
Quy tắc bắt buộc:
1. Chỉ trả lời dựa trên các Document trong context, không dùng kiến thức bên ngoài.
2. Sau mỗi khẳng định, ghi citation dạng [n] với n là số của Document chứa bằng chứng, ví dụ [1] hoặc [2][3].
3. Nếu context không có đủ bằng chứng để trả lời, chỉ trả lời đúng câu: "{REFUSAL}"
4. Trả lời ngắn gọn, chính xác, bằng tiếng Việt; giữ nguyên con số, thời hạn, tên văn bản như trong context."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context (giảm lost-in-the-middle)."""
    if len(chunks) <= 2:
        return list(chunks)
    return chunks[::2] + chunks[1::2][::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có số citation, title và source label."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        parts.append(
            f"[Document {chunk.get('citation', index)} | Title: {metadata['title']} | "
            f"Source: {metadata['source']}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo LLM_PROVIDER, trả text thuần."""
    model = LLM_MODEL or DEFAULT_MODELS.get(LLM_PROVIDER, "")
    if LLM_PROVIDER == "openai":
        from openai import OpenAI

        # OpenAI() tự đọc OPENAI_API_KEY và OPENAI_BASE_URL (proxy OpenAI-compatible) từ env.
        response = OpenAI(timeout=60).chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content or ""
    if LLM_PROVIDER == "gemini":
        from google import genai

        response = genai.Client(api_key=os.getenv("GEMINI_API_KEY")).models.generate_content(
            model=model,
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                max_output_tokens=MAX_TOKENS,
            ),
        )
        return response.text or ""
    if LLM_PROVIDER == "anthropic":
        import anthropic

        response = anthropic.Anthropic(timeout=60).messages.create(
            model=model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return "".join(block.text for block in response.content if block.type == "text")
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def extract_citations(answer: str, source_count: int) -> list[int]:
    """Số citation [n] trong answer map được về sources[n-1]."""
    return sorted({int(n) for n in re.findall(r"\[(\d+)\]", answer) if 1 <= int(n) <= source_count})


def generate_from_chunks(query: str, chunks: list[dict]) -> dict:
    """Sinh câu trả lời có citation từ chunks đã retrieve (dùng chung cho app và evaluation)."""
    if not chunks:
        return {"answer": REFUSAL, "sources": [], "retrieval_source": "none", "citations": []}

    numbered = [{**chunk, "citation": index} for index, chunk in enumerate(chunks, 1)]
    context = format_context(reorder_for_llm(numbered))
    user_message = f"Context:\n{context}\n\nQuestion: {query}"
    retrieval_source = chunks[0]["retrieval_method"]
    if retrieval_source not in {"hybrid", "pageindex"}:
        retrieval_source = "hybrid"
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message).strip()
    except Exception as error:
        logger.warning("LLM provider failed: %s", error)
        return {
            "answer": REFUSAL,
            "sources": chunks,
            "retrieval_source": retrieval_source,
            "citations": [],
            "error": f"{type(error).__name__}: {error}",
        }
    return {
        "answer": answer or REFUSAL,
        "sources": chunks,
        "retrieval_source": retrieval_source,
        "citations": extract_citations(answer, len(chunks)),
    }


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    return generate_from_chunks(query, retrieve(query, top_k=top_k))


if __name__ == "__main__":
    from .contracts import validate_generation_result

    for question in ("Ai không có quyền thành lập doanh nghiệp?", "Công thức nấu phở bò?"):
        result = generate_with_citation(question)
        validate_generation_result(result)
        print(question, "->", result["answer"], result["citations"], result.get("error", ""))
