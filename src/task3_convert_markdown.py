"""
Task 3 — Chuẩn hóa tài liệu sang Markdown.

Hướng dẫn:
    1. Đọc PDF/DOCX từ data/landing/legal/  →  data/standardized/legal/
    2. Đọc JSON từ data/landing/news/        →  data/standardized/news/
    3. Mỗi output gồm file .md (nội dung) và .json sidecar (metadata).
    4. Chạy acceptance test để kiểm tra.

Cài markitdown (nếu chưa có):
    pip install markitdown
"""

import json
import re
from pathlib import Path

from markitdown import MarkItDown

# ---- Đường dẫn ----
BASE_DIR = Path(__file__).parent.parent
LANDING_DIR = BASE_DIR / "data" / "landing"
STANDARDIZED_DIR = BASE_DIR / "data" / "standardized"


# ============================================================
#  Helper chung
# ============================================================

def _sanitize_filename(name: str) -> str:
    """Bỏ dấu, ký tự đặc biệt; giữ chữ thường + gạch nối."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "untitled"


def _write_output(
    output_dir: Path,
    stem: str,
    markdown_content: str,
    metadata: dict,
) -> None:
    """Ghi file .md và sidecar .json vào output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = output_dir / f"{stem}.md"
    md_path.write_text(markdown_content.strip(), encoding="utf-8")

    json_path = output_dir / f"{stem}.json"
    json_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  ✓ {md_path.relative_to(BASE_DIR)}  "
          f"({len(markdown_content):,} chars)")


# ============================================================
#  Nhánh 1: Tài liệu chính sách (PDF / DOCX)
# ============================================================

def convert_legal() -> int:
    """
    Chuyển đổi mọi file PDF/DOCX trong data/landing/legal/
    sang Markdown chuẩn hóa trong data/standardized/legal/.

    Trả về số file đã chuyển đổi thành công.
    """
    landing = LANDING_DIR / "legal"
    output = STANDARDIZED_DIR / "legal"

    if not landing.exists():
        print("⚠ data/landing/legal/ không tồn tại. Chạy Task 1 trước.")
        return 0

    md_converter = MarkItDown()
    count = 0

    for filepath in sorted(landing.iterdir()):
        if filepath.suffix.lower() not in (".pdf", ".doc", ".docx"):
            continue

        try:
            result = md_converter.convert(str(filepath))
            markdown_text = result.text_content or ""
        except Exception as exc:
            print(f"  ✗ Lỗi chuyển đổi {filepath.name}: {exc}")
            continue

        if not markdown_text.strip():
            print(f"  ⚠ {filepath.name} cho nội dung rỗng, bỏ qua.")
            continue

        # Metadata sidecar
        stem = _sanitize_filename(filepath.stem)
        metadata = {
            "source": str(filepath.relative_to(BASE_DIR)),
            "title": filepath.stem.replace("-", " ").replace("_", " ").title(),
            "doc_type": "legal",
            "url": None,
        }

        _write_output(output, stem, markdown_text, metadata)
        count += 1

    print(f"\nLegal: đã chuyển {count} file → {output.relative_to(BASE_DIR)}")
    return count


# ============================================================
#  Nhánh 2: Bài viết / tin tức (JSON từ Crawl4AI)
# ============================================================

def convert_news() -> int:
    """
    Đọc mọi file JSON trong data/landing/news/
    và ghi thành Markdown + sidecar trong data/standardized/news/.

    Trả về số file đã chuyển đổi thành công.
    """
    landing = LANDING_DIR / "news"
    output = STANDARDIZED_DIR / "news"

    if not landing.exists():
        print("⚠ data/landing/news/ không tồn tại. Chạy Task 2 trước.")
        return 0

    count = 0

    for filepath in sorted(landing.glob("*.json")):
        try:
            raw = json.loads(filepath.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  ✗ Lỗi đọc {filepath.name}: {exc}")
            continue

        # Lấy nội dung markdown từ crawl
        markdown_text = raw.get("content_markdown", "").strip()
        if not markdown_text:
            print(f"  ⚠ {filepath.name} không có content_markdown, bỏ qua.")
            continue

        # Metadata
        url = raw.get("url")
        title = raw.get("title", filepath.stem)
        date_crawled = raw.get("date_crawled", "")

        stem = _sanitize_filename(title)
        # Tránh tên file quá dài
        if len(stem) > 80:
            stem = stem[:80].rstrip("-")

        metadata = {
            "source": str(filepath.relative_to(BASE_DIR)),
            "title": title,
            "doc_type": "news",
            "url": url,
            "date_crawled": date_crawled,
        }

        _write_output(output, stem, markdown_text, metadata)
        count += 1

    print(f"\nNews: đã chuyển {count} file → {output.relative_to(BASE_DIR)}")
    return count


# ============================================================
#  Main
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Task 3 — Chuẩn hóa tài liệu sang Markdown")
    print("=" * 60)

    n_legal = convert_legal()
    print()
    n_news = convert_news()

    print()
    print("=" * 60)
    total = n_legal + n_news
    if total == 0:
        print("⚠ Không có file nào được chuyển đổi. Kiểm tra lại Task 1 & 2.")
    else:
        print(f"✅ Hoàn thành: {n_legal} legal + {n_news} news = {total} file")
    print("=" * 60)


if __name__ == "__main__":
    main()