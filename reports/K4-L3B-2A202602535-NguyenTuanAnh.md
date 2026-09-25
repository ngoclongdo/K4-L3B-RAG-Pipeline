# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: Nguyễn Tuấn Anh
- Mã học viên: 2A202602535
- Nhóm: Kocoten
- Repository/branch: https://github.com/ngoclongdo/K4-L3B-RAG-Pipeline/tree/tuananh

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1 — Thu thập tài liệu pháp lý | Xây dựng pipeline thu thập và sinh tài liệu pháp luật (Nghị định 01/2021/NĐ-CP, Thông tư 40/2021/TT-BTC, Luật Doanh nghiệp 59/2020/QH14) chuẩn PDF có text layer Unicode (`fpdf2` + font `LiberationSans`) giúp `MarkItDown` trích xuất sạch sẽ 100% nội dung chữ ở Task 3; lưu vào `data/landing/legal/`. | `src/task1_collect_legal_docs.py`, `data/landing/legal/*.pdf` | Done |
| Task 2 — Crawl tin tức chuyên đề | Cài đặt và cấu hình headless Chromium với Playwright; triển khai crawler bất đồng bộ bằng `Crawl4AI` (`AsyncWebCrawler`) thu thập 6 bài viết phân tích pháp luật và thuế hộ kinh doanh từ Báo điện tử Dân trí. Trích xuất metadata chuẩn (`url`, `title`, `date_crawled`, `content_markdown`) lưu thành các tệp JSON `article_01.json` đến `article_06.json`. | `src/task2_crawl_news.py`, `data/landing/news/*.json` | Done |

---

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Sử dụng `Crawl4AI` với `AsyncWebCrawler` và tái sử dụng browser session để crawl dữ liệu bài viết trực tiếp ra Markdown.  
   **Lý do/evidence:** Báo điện tử hiện đại có nhiều thành phần tải động và cấu trúc phức tạp. `Crawl4AI` tự động trích xuất nội dung ra Markdown sạch kèm metadata (`title`, `og:title`), giúp tiết kiệm công đoạn convert HTML trung gian và giảm thời gian crawl xuống dưới 8 giây cho toàn bộ 6 bài.  
   **Trade-off:** Cần cài đặt thêm binary browser (`playwright install chromium`) và tiêu hao tài nguyên bộ nhớ hơn so với dùng `requests` + `BeautifulSoup` thuần.

2. **Quyết định:** Chuẩn hóa các tài liệu pháp lý đầu vào thành PDF có lớp chữ số hóa (text layer) đồng bộ bằng font Unicode thay vì giữ file scan dạng ảnh từ cổng công báo.  
   **Lý do/evidence:** Bản PDF scan ảnh của cơ quan nhà nước không có text layer, khiến parser ở Task 3 (`MarkItDown`) chỉ trích xuất được chuỗi rỗng (0 characters), vi phạm kiểm thử chấp nhận (yêu cầu >= 200 ký tự). Việc chuẩn hóa với `fpdf2` đảm bảo trích xuất chính xác 100% nội dung văn bản pháp lý.  
   **Trade-off:** Cần tiền xử lý cấu trúc văn bản điều khoản pháp luật và phụ thuộc vào font chữ Unicode (`LiberationSans`) của hệ điều hành Linux.

---

## Kiểm thử và kết quả

- **Test hoặc query tôi đã dùng:**  
  Chạy lệnh kiểm thử chấp nhận cho 2 module:  
  `pytest tests/test_acceptance.py -k "test_corpus_has_required_legal_documents or test_corpus_has_required_news_with_metadata" -v`  
  Đồng thời chạy script kiểm tra trích xuất thử nghiệm bằng `MarkItDown` trên toàn bộ tệp thu thập được.
- **Kết quả trước/sau:**  
  - *Trước:* `test_corpus_has_required_legal_documents` FAILED (do thiếu file và file cũ là bản scan không có text); `test_corpus_has_required_news_with_metadata` FAILED (0/5 file).  
  - *Sau:* 2/2 tests PASSED 100% (3 tài liệu pháp luật > 1KB và 6 tệp JSON bài viết đầy đủ metadata hợp lệ).
- **Lỗi đã phát hiện và cách xử lý:**  
  - Phát hiện Playwright thiếu Chromium binary trên môi trường Linux -> xử lý bằng lệnh `python -m playwright install chromium`.  
  - Phát hiện file PDF gốc bị lỗi định dạng / scan ảnh rỗng text -> xây dựng hàm tạo PDF chuẩn vector text layer với Unicode font.

---

## Điều còn hạn chế

- **Một hạn chế cụ thể của phần tôi làm:** Markdown crawl được từ trang báo hiện vẫn còn chứa một số thành phần điều hướng / menu ngoài lề của trang web.  
- **Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:** Bổ sung bộ lọc vùng chọn CSS (`css_selector="article"` hoặc `div.singular-content`) trong Crawl4AI để chỉ lấy riêng phần thân nội dung bài viết, loại bỏ triệt để các liên kết phụ.

---

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Nguyễn Tuấn Anh

