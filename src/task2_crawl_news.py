"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from crawl4ai import AsyncWebCrawler


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://dantri.com.vn/kinh-doanh/bo-tai-chinh-sap-co-huong-dan-giam-30-thue-cho-ho-kinh-doanh-20260925162029275.htm",
    "https://dantri.com.vn/kinh-doanh/dung-loa-tingting-ho-kinh-doanh-can-dac-biet-luu-y-dong-tien-20260922145818158.htm",
    "https://dantri.com.vn/kinh-doanh/ho-kinh-doanh-thu-duoi-10-ty-dong-sap-duoc-tu-chon-cach-tinh-thue-20260921093144363.htm",
    "https://dantri.com.vn/kinh-doanh/de-xuat-chi-tiet-viec-giam-30-thue-cho-ho-kinh-doanh-doanh-nghiep-20260907211143863.htm",
    "https://dantri.com.vn/kinh-doanh/huong-dan-thue-hang-tram-trang-khien-ho-kinh-doanh-ngop-tra-cuu-ra-sao-20260911161924344.htm",
    "https://dantri.com.vn/kinh-doanh/de-chinh-sach-ho-tro-thuc-su-tao-dong-luc-cho-ho-kinh-doanh-20260824181039633.htm",
]


async def crawl_article(url: str, crawler: AsyncWebCrawler | None = None) -> dict:
    """Crawl một bài viết bằng Crawl4AI và trả về metadata chuẩn."""
    if crawler is not None:
        result = await crawler.arun(url=url)
    else:
        async with AsyncWebCrawler() as default_crawler:
            result = await default_crawler.arun(url=url)

    metadata = result.metadata or {}
    title = (
        metadata.get("title")
        or metadata.get("og:title")
        or "Unknown Article"
    )
    if " | Báo Dân trí" in title:
        title = title.replace(" | Báo Dân trí", "").strip()

    markdown_content = result.markdown or ""

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": markdown_content,
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON trong data/landing/news/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    async with AsyncWebCrawler() as crawler:
        for index, url in enumerate(ARTICLE_URLS, 1):
            try:
                article = await crawl_article(url, crawler=crawler)
                output = DATA_DIR / f"article_{index:02d}.json"
                output.write_text(
                    json.dumps(article, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                print(f"Saved: {output.name} — {article['title']}")
            except Exception as error:
                print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
