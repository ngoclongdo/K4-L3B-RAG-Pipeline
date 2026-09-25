# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/K4-L3A-2A202603006-PhungThanhAn.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: Phùng Thành An 
- Mã học viên: 2A202603006
- Nhóm: Kocoten
- Repository/branch: https://github.com/ngoclongdo/K4-L3B-RAG-Pipeline/tree/thanhan

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 3 — chuẩn hóa corpus | Implement `convert_legal_docs()` (MarkItDown cho PDF/DOC/DOCX) và `convert_news_articles()` (JSON → Markdown kèm header title/source/date cho citation); xử lý idempotent, bỏ qua nội dung rỗng, log lỗi từng file, cảnh báo khi thiếu số lượng tối thiểu | `src/task3_convert_markdown.py` — branch `thanhan` (hash: `<điền-sau-khi-push>`) | Done |
| Task 4 — load & chunk | Implement `load_documents()` (Document theo contract, id ổn định theo đường dẫn file, parse `title`/`url` từ header news) và `chunk_documents()` (RecursiveCharacterTextSplitter, id `<doc_id>::chunk-<i>`, loại chunk rỗng, không mutate input) | `src/task4_chunking_indexing.py` — branch `thanhan` | Done |
| Task 4 — embedding & indexing | Implement `embed_texts()` dispatch theo `EMBEDDING_PROVIDER` (sentence_transformers/openai/gemini, cache model), `get_collection()` cosine, `index_to_vectorstore()` upsert theo batch + sanitize metadata; `run_pipeline()` in thống kê chunk cho báo cáo nhóm | `src/task4_chunking_indexing.py` — branch `thanhan` | Done |
| Kiểm thử phần mình làm | Chạy `pytest tests/test_acceptance.py -q` cho dữ liệu chuẩn hóa và `pytest tests/test_contracts.py -q` cho invariants của Task 4; viết script kiểm tra bổ sung: convert PDF Unicode, ID ổn định khi chạy lại, không trùng file khi re-convert | output `pytest` + log chạy trên branch `thanhan` | Done |
| Phối hợp contract với Task 5/6 | Chốt `embed_texts()` là entrypoint dùng chung corpus/query để bạn làm Task 5 import lại, tránh lệch model/dimension | `docs/MODULE_CONTRACTS.md`, signature trong `src/task4_chunking_indexing.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Giữ metadata nguồn xuyên pipeline bằng "vòng khép kín": Task 3 ghi header chuẩn (`# title`, `**Source:** url`, `**Crawled:** date`) vào Markdown của news, Task 4 parse ngược header này để điền `metadata.title`/`metadata.url`.
   **Lý do/evidence:** Contract bắt buộc `source/title/doc_type/url` đi xuyên suốt tới `sources` của GenerationResult; nếu chỉ lấy tên file, citation ở UI không mở được URL bài báo. Đối chiếu: chunk của `news/article_xx.md` mang đúng URL Dân trí gốc sau khi index.
   **Trade-off:** Parser phụ thuộc đúng format header — nếu nhóm đổi template Markdown ở Task 3 thì phải sửa regex ở Task 4; chunk đầu của bài news hơi ngắn hơn vì chứa header.

2. **Quyết định:** ID ổn định `<đường-dẫn-file>::chunk-<index>` + upsert theo batch vào ChromaDB (sanitize `None → ""` trong metadata).
   **Lý do/evidence:** Contract yêu cầu chạy lại index không nhân bản dữ liệu: `load_documents` + `chunk_documents` chạy hai lần cho ra dãy chunk id giống hệt nhau, upsert ghi đè theo id nên `collection.count()` không tăng sau lần chạy thứ hai. Sanitize `url=None → ""` để không phụ thuộc việc phiên bản Chroma có chấp nhận giá trị `None` hay không (contract vẫn thỏa vì validator nhận `str`).
   **Trade-off:** Nếu xóa bớt file khỏi corpus, chunk cũ vẫn sót lại trong Chroma (orphan) — `run_pipeline()` đã thêm cảnh báo khi `count > số chunk hiện tại`, và nhóm thống nhất xóa `chroma_db/` index lại khi đổi corpus lớn.

## Kiểm thử và kết quả

- **Test hoặc query tôi đã dùng:**
  - `pytest tests/test_acceptance.py -q` — kiểm tra ≥3 legal, ≥5 news, mỗi Markdown chuẩn hóa ≥200 ký tự.
  - `pytest tests/test_contracts.py -q` — riêng các case của Task 4: `test_chunk_documents_preserves_identity_and_metadata` (unique id, `chunk_index` tuần tự, dài ≤ `CHUNK_SIZE*1.1`, giữ `metadata.source`).
  - Script kiểm tra thủ công: convert một PDF tiếng Việt sinh bằng fpdf2 (kiểm tra MarkItDown trích Unicode có dấu), chunk cùng corpus hai lần để so sánh dãy id, đếm file trước/sau khi chạy lại Task 3.
- **Kết quả trước/sau nếu có:** Trước khi loại chunk rỗng, text splitter đôi khi sinh chunk chỉ chứa khoảng trắng → vi phạm rule "content không rỗng" của validator; sau khi `strip()` + bỏ qua, mọi chunk đều pass `validate_document(require_chunk=True)`. ID chunk ổn định tuyệt đối giữa các lần chạy.
- **Lỗi đã phát hiện và cách xử lý:**
  - PDF tạo bằng font không nhúng Unicode khiến MarkItDown trích text hỏng dấu → chuẩn hóa lại đầu vào Task 1 dùng TTF Unicode (DejaVu/Liberation) thì trích đúng.
  - Bản nháy đầu của `embed_texts()` khai báo `global EMBEDDING_MODEL` sau khi đã dùng biến → nguy cơ `SyntaxError`; refactor về hằng số module đọc từ `.env` lúc import + cache model kèm kiểm tra tên model khi đổi.

## Điều còn hạn chế

- **Một hạn chế cụ thể của phần tôi làm:** Chunk theo độ dài cố định 500 ký tự đôi khi cắt giữa danh sách khoản a/b/c trong một điều luật, làm mất ngữ cảnh "Điều …" ở chunk sau; ngoài ra nhánh embedding `openai`/`gemini` là pass-through theo SDK, nhóm mới verify kỹ nhánh `sentence_transformers` vì đó là provider trong `.env` của nhóm.
- **Nếu nhóm có thêm thời gian, thay đổi đầu tiên tôi sẽ làm:** Structure-aware chunking cho văn bản pháp luật — tách theo ranh giới "Điều/Khoản" bằng regex trước khi áp splitter, và thêm bước dọn chunk orphan trong Chroma khi corpus thay đổi thay vì cảnh báo thủ công.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Phùng Thành An
