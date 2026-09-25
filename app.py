import html
import re

import streamlit as st
from dotenv import load_dotenv

from src.task4_chunking_indexing import EMBEDDING_MODEL, get_collection
from src.task6_lexical_search import tokenize
from src.task9_retrieval_pipeline import SCORE_THRESHOLD
from src.task10_generation import LLM_MODEL, LLM_PROVIDER, REFUSAL, generate_with_citation


load_dotenv()

st.set_page_config(page_title="Trợ lý Hộ kinh doanh", page_icon="⚖️", layout="wide")

SAMPLE_QUESTIONS = [
    "Ai không có quyền thành lập và quản lý doanh nghiệp?",
    "Hộ kinh doanh có doanh thu bao nhiêu thì không phải nộp thuế?",
    "Đề xuất giảm 30% thuế cho hộ kinh doanh áp dụng với ai?",
    "Công thức nấu phở bò?",
]
STOPWORDS = {"và", "của", "có", "là", "cho", "các", "được", "không", "thì", "bao", "nhiêu", "ai", "gì", "nào", "hộ", "kinh", "doanh", "phải"}
METHOD_LABELS = {"hybrid": "Hybrid (Dense + BM25, RRF)", "pageindex": "PageIndex fallback", "none": "Không có nguồn"}


def highlight(text: str, query: str) -> str:
    """Escape HTML rồi tô sáng các từ của câu hỏi xuất hiện trong nguồn."""
    escaped = html.escape(text)
    terms = sorted({t for t in tokenize(query) if len(t) > 1 and t not in STOPWORDS}, key=len, reverse=True)
    if terms:
        pattern = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, terms)) + r")(?!\w)", re.IGNORECASE)
        escaped = pattern.sub(r"<mark>\1</mark>", escaped)
    return escaped.replace("\n", "<br>")


def render_sources(result: dict, query: str) -> None:
    sources = result["sources"]
    if result.get("error"):
        st.warning(f"LLM provider lỗi nên trả safe refusal. Chi tiết: {result['error']}")
    if not sources:
        return
    cited = set(result.get("citations", []))
    st.caption(
        f"Retrieval: **{METHOD_LABELS.get(result['retrieval_source'], result['retrieval_source'])}** · "
        f"{len(sources)} nguồn · đã trích dẫn: {', '.join(f'[{n}]' for n in sorted(cited)) or 'không'}"
    )
    with st.expander(f"Nguồn đã dùng ({len(sources)})", expanded=bool(cited)):
        for index, source in enumerate(sources, 1):
            metadata = source["metadata"]
            badge = "✅ được trích dẫn" if index in cited else "chưa trích dẫn"
            link = f" · [mở nguồn]({metadata['url']})" if metadata.get("url") else ""
            st.markdown(
                f"**[{index}] {metadata['title']}** · `{metadata['doc_type']}` · `{metadata['source']}` "
                f"· chunk {metadata['chunk_index']} · {source['retrieval_method']} score "
                f"`{source['score']:.4f}` · {badge}{link}"
            )
            st.markdown(
                f"<div class='source'>{highlight(source['content'], query)}</div>",
                unsafe_allow_html=True,
            )


st.markdown(
    """<style>
    .source {font-size: 0.9rem; border-left: 3px solid #999; padding: 0.4rem 0.8rem; margin-bottom: 1rem;}
    mark {background: #ffe58f; color: #111; padding: 0 2px; border-radius: 2px;}
    </style>""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("⚖️ Trợ lý Hộ kinh doanh")
    st.caption(
        "Hỏi đáp về thành lập, đăng ký hộ kinh doanh/doanh nghiệp và thuế đối với hộ kinh doanh, "
        "dựa trên Luật Doanh nghiệp 59/2020/QH14, Nghị định 01/2021/NĐ-CP, Thông tư 40/2021/TT-BTC "
        "và 6 bài báo Dân trí."
    )
    top_k = st.slider("Số chunks đưa vào LLM (top_k)", 3, 10, 5)
    st.markdown("**Câu hỏi mẫu**")
    for sample in SAMPLE_QUESTIONS:
        if st.button(sample, use_container_width=True):
            st.session_state.pending = sample
    if st.button("Xóa hội thoại"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    try:
        chunk_count = get_collection().count()
    except Exception as error:
        chunk_count = f"lỗi: {error}"
    st.caption(
        f"Chunks đã index: **{chunk_count}**  \n"
        f"Embedding: `{EMBEDDING_MODEL}`  \n"
        f"LLM: `{LLM_PROVIDER}` / `{LLM_MODEL or 'default'}`  \n"
        f"Fallback threshold (dense cosine): `{SCORE_THRESHOLD}`"
    )

st.title("Hỏi đáp pháp luật cho hộ kinh doanh")
st.caption(
    "Câu trả lời chỉ dựa trên tài liệu đã thu thập, mỗi ý có citation [n] ứng với nguồn bên dưới. "
    f"Nếu không đủ bằng chứng, chatbot trả lời: “{REFUSAL}”"
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message["result"], message["query"])

query = st.chat_input("Nhập câu hỏi...") or st.session_state.pop("pending", None)

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm nguồn và sinh câu trả lời..."):
            try:
                result = generate_with_citation(query, top_k)
            except Exception as error:
                result = {"answer": REFUSAL, "sources": [], "retrieval_source": "none", "error": str(error)}
        st.markdown(result["answer"])
        render_sources(result, query)

    st.session_state.messages.append(
        {"role": "assistant", "content": result["answer"], "result": result, "query": query}
    )
