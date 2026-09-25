"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import re
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
NEWS_FOOTER_MARKER = "Không bỏ lỡ tin mới"


def join_wrapped_lines(text: str) -> str:
    """PDF ngắt dòng cứng giữa câu thành đoạn mới; nối lại khi dòng sau bắt đầu bằng chữ thường."""
    text = re.sub(r"\n*\f\n*", "\n\n", text)
    text = re.sub(
        r"([^\s.:;!?])\n\n(\S)",
        lambda match: f"{match[1]} {match[2]}" if match[2].islower() else match[0],
        text,
    )
    return re.sub(r"[ \t]{2,}", " ", text)


def clean_news_markdown(text: str) -> str:
    """Bỏ menu, quảng cáo, danh sách link của trang báo; giữ đoạn văn có nội dung."""
    # ponytail: heuristic đếm từ ngoài link, chưa bắt được footer dài; dùng selector theo site nếu cần
    text = text.split(NEWS_FOOTER_MARKER)[0]
    kept = []
    for line in IMAGE.sub("", text).splitlines():
        plain_words = re.findall(r"\w+", LINK.sub("", line))
        is_heading = line.lstrip().startswith("#") and not LINK.search(line)
        if len(plain_words) >= 8 or is_heading:
            kept.append(LINK.sub(r"\1", line).strip())
    return "\n\n".join(kept)


def write_markdown(path: Path, text: str) -> None:
    if not text.strip():
        print(f"Skipped empty: {path.name}")
        return
    path.write_text(text.strip() + "\n", encoding="utf-8")
    print(f"Saved: {path}")


def convert_legal_docs() -> None:
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()
    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() in {".pdf", ".doc", ".docx"}:
            result = converter.convert(str(path))
            write_markdown(output_dir / f"{path.stem}.md", join_wrapped_lines(result.text_content))


def convert_news_articles() -> None:
    import json

    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data.get("content_markdown", "").strip():
            print(f"Skipped empty: {path.name}")
            continue
        header = (
            f"# {data['title']}\n\n"
            f"**Source:** {data['url']}\n\n"
            f"**Crawled:** {data['date_crawled']}\n\n---\n\n"
        )
        write_markdown(output_dir / f"{path.stem}.md", header + clean_news_markdown(data["content_markdown"]))


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
