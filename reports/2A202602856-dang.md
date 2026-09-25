# Individual contribution report

## Thông tin

- Họ và tên: Phùng Đức Đăng
- Mã học viên: 2A202602856
- Nhóm:
- Repository/branch: K4-L3B-RAG-Pipeline / `dangpd`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 5 — Semantic search | Embed query bằng `embed_texts()` dùng chung với Task 4, query ChromaDB, đổi cosine distance → similarity `max(0, 1 - d)`, trả `SearchResult` (`retrieval_method="dense"`), sort giảm dần, cắt `top_k` | `src/task5_semantic_search.py` | Done (khung); chờ Task 4 để chạy end-to-end |
| Task 6 — Lexical search (BM25) | Tokenize bằng regex `\w+` (giữ dấu tiếng Việt, bỏ dấu câu), build BM25 trên cùng corpus chunks của Task 4 (nạp tự động qua `load_documents()` + `chunk_documents()` khi `CORPUS` rỗng), loại chunk không chứa từ nào của query, trả `SearchResult` (`retrieval_method="bm25"`) | `src/task6_lexical_search.py` | Done (khung); chờ Task 3–4 để có corpus thật |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng `BM25Plus` thay vì `BM25Okapi`.
   **Lý do/evidence:** Với corpus nhỏ, `BM25Okapi` cho IDF = log((N−n+0.5)/(n+0.5)) = 0 khi một term xuất hiện ở đúng một nửa số chunk (ví dụ corpus test 2 chunk), nên mọi score = 0 và chunk đúng không lên đầu. `BM25Plus` luôn cho IDF dương. Vì BM25Plus cộng thêm δ cho cả chunk không khớp, tôi lọc theo giao tập token thay vì `score > 0`.
   **Trade-off:** Score BM25Plus không so sánh trực tiếp được với BM25Okapi. Điều này không ảnh hưởng vì RRF (Task 7) chỉ dùng thứ hạng.

2. **Quyết định:** Score dense là cosine similarity gốc `1 - distance` (collection dùng `hnsw:space=cosine`), không chuẩn hoá thêm.
   **Lý do/evidence:** Contract yêu cầu fallback ở Task 9 so threshold với cosine score gốc của dense search, nên score này phải giữ nguyên nghĩa.
   **Trade-off:** Thang điểm của dense (0–1) và BM25 (không giới hạn) khác nhau, nên không cộng trực tiếp được mà phải fuse bằng RRF.

## Kiểm thử và kết quả

- Test đã dùng: `pytest tests/test_contracts.py -q -k "semantic or lexical"`, dùng mock collection/corpus, không gọi network.
- Kết quả: 2/2 passed (`test_semantic_search_uses_shared_embedding_and_contract`, `test_lexical_search_returns_bm25_contract`).
- Lỗi đã phát hiện và cách xử lý: code gợi ý dùng `BM25Okapi` + lọc `score <= 0`. Với corpus test 2 chunk, cách này trả về list rỗng và làm hỏng `output[0]`. Tôi đã sửa bằng `BM25Plus` + lọc theo token overlap. Query rỗng hoặc `top_k <= 0` trả `[]`.

## Điều còn hạn chế

- Hạn chế: Chưa chạy được trên dữ liệu thật vì Task 3 (convert Markdown) và Task 4 (chunk/embed/index) chưa có code. BM25 build lại index ở mỗi query, O(N). Tokenize theo khoảng trắng nên chưa tách từ ghép tiếng Việt (ví dụ "học phí" thành 2 token).
- Nếu có thêm thời gian: cache BM25 index sau lần build đầu, thử tách từ tiếng Việt (`underthesea`/`pyvi`), và đo recall dense vs BM25 trên golden dataset.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-25
- Tên thành viên: Phùng Đức Đăng
