"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.

Thiết kế:
    - Tên file output = stem của file input, nên chạy lại sẽ GHI ĐÈ đúng file cũ
      (idempotent), không sinh bản sao.
    - File tin tức luôn có header chuẩn gồm title / URL nguồn / ngày crawl để
      Task 4 trích metadata (url, title) cho citation.
    - Nội dung rỗng (convert thất bại, markdown trắng) bị bỏ qua thay vì tạo
      file rỗng làm hỏng acceptance test.
    - Lỗi từng file được log và không làm dừng toàn bộ batch.
"""

import json
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

LEGAL_EXTENSIONS = {".pdf", ".doc", ".docx"}


def convert_legal_docs() -> int:
    """Convert PDF/DOCX trong data/landing/legal sang standardized/legal.

    Trả về số file convert thành công.
    """
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not legal_dir.is_dir():
        print(f"Missing directory: {legal_dir}")
        return 0

    converter = MarkItDown()
    converted = 0

    for path in sorted(legal_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in LEGAL_EXTENSIONS:
            continue
        try:
            result = converter.convert(str(path))
            text = (result.text_content or "").strip()
            if not text:
                print(f"Skipped (empty content): {path.name}")
                continue

            output_path = output_dir / f"{path.stem}.md"
            output_path.write_text(text + "\n", encoding="utf-8")
            converted += 1
            print(f"Converted: {path.name} -> standardized/legal/{output_path.name} "
                  f"({len(text):,} chars)")
        except Exception as error:
            # Một file lỗi không được làm hỏng cả batch; kiểm tra lại file đó.
            print(f"Failed: {path.name} -- {error}")

    print(f"Legal documents converted: {converted}")
    return converted


def convert_news_articles() -> int:
    """Convert JSON bài viết trong data/landing/news sang standardized/news.

    Header Markdown giữ metadata nguồn để Task 4 parse ngược lại cho citation.
    Trả về số file convert thành công.
    """
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not news_dir.is_dir():
        print(f"Missing directory: {news_dir}")
        return 0

    converted = 0

    for path in sorted(news_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))

            title = str(data.get("title") or path.stem).strip()
            url = str(data.get("url") or "").strip()
            date_crawled = str(data.get("date_crawled") or "").strip()
            body = str(data.get("content_markdown") or "").strip()

            if not body:
                print(f"Skipped (empty content_markdown): {path.name}")
                continue

            header = (
                f"# {title}\n\n"
                f"**Source:** {url}\n\n"
                f"**Crawled:** {date_crawled}\n\n---\n\n"
            )

            output_path = output_dir / f"{path.stem}.md"
            output_path.write_text(header + body + "\n", encoding="utf-8")
            converted += 1
            print(f"Converted: {path.name} -> standardized/news/{output_path.name} "
                  f"({len(header) + len(body):,} chars)")
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            print(f"Failed: {path.name} -- {error}")

    print(f"News articles converted: {converted}")
    return converted


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    legal_count = convert_legal_docs()
    news_count = convert_news_articles()

    # Cảnh báo sớm nếu chưa đủ số lượng tối thiểu của acceptance test.
    if legal_count < 3:
        print(f"WARNING: chi co {legal_count}/3 legal documents toi thieu.")
    if news_count < 5:
        print(f"WARNING: chi co {news_count}/5 news articles toi thieu.")

    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
