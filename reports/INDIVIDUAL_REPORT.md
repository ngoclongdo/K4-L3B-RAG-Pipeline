# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: Đỗ Nguyễn Ngọc Long
- Mã học viên: 2A202602390
- Nhóm:
- Repository/branch: https://github.com/ngoclongdo/K4-L3B-RAG-Pipeline/tree/long

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| RRF Reranking (Task 7) | Triển khai thuật toán Reciprocal Rank Fusion kết hợp kết quả từ Dense và Lexical search theo rank, chống mutate item gốc và loại bỏ duplicate | `src/task7_reranking.py` | Done |
| PageIndex Fallback (Task 8) | Xây dựng pipeline fallback vectorless qua PageIndex API: tự động upload văn bản legal (PDF), cache document IDs và parse SearchResult chuẩn schema | `src/task8_pageindex_vectorless.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Sử dụng xếp hạng qua RRF (Reciprocal Rank Fusion) thay vì cộng gộp trực tiếp cosine score và BM25 score.  
   **Lý do/evidence:** Cosine similarity (thang đo [-1, 1] hoặc [0, 1]) và BM25 score (thang đo không chặn trên, phụ thuộc độ dài và tần suất từ) không cùng phân phối và thang đo. RRF tính điểm dựa trên thứ bậc `1 / (k + rank)`, giúp cân bằng công bằng giữa 2 nhánh tìm kiếm.  
   **Trade-off:** Mất đi khoảng cách điểm số tuyệt đối giữa các văn bản trong cùng một nhánh, nhưng loại bỏ hoàn toàn nguy cơ điểm BM25 áp đảo điểm dense.

2. **Quyết định:** Thiết kế cơ chế Fault-Tolerance và Caching cho PageIndex fallback.  
   **Lý do/evidence:** PageIndex là dịch vụ ngoài (external service), có thể gặp độ trễ mạng, timeout, hoặc hết quota/thiếu API key. Thêm `try/except` với fallback an toàn trả về danh sách rỗng (hoặc giữ hybrid kết quả trước đó) giúp toàn bộ RAG pipeline không bị crash. Caching `data/pageindex_cache.json` tránh upload lại tài liệu tốn thời gian.  
   **Trade-off:** Cần thêm mã nguồn quản lý file cache local và logic polling trạng thái retrieval từ API.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
  - `pytest tests/test_contracts.py -k test_rrf_uses_rank_deduplicates_and_marks_hybrid -v`
  - Chạy thử nghiệm độc lập `rerank_rrf()` với các mock ranked lists chứa trùng lặp ID và khác biệt điểm số.
  - Chạy thử nghiệm `pageindex_search()` trong điều kiện không có API key / key hợp lệ để kiểm chứng tính bền bỉ của pipeline.
- Kết quả trước/sau nếu có:
  - Trước: Task 7 & Task 8 ném `NotImplementedError`.
  - Sau: Pass 100% contract test cho Task 7. Task 8 trả kết quả chuẩn contract `SearchResult` (với `retrieval_method="pageindex"`) và không làm gián đoạn luồng pipeline.
- Lỗi đã phát hiện và cách xử lý:
  - Khi gán điểm RRF, cần dùng `copy.deepcopy()` trên từng `SearchResult` để tránh làm biến đổi (mutate) danh sách gốc của Dense và BM25.
  - Xử lý timeout khi poll kết quả từ PageIndex API để tránh blocking pipeline quá lâu.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: PageIndex hiện tại mới chỉ tự động quét các file PDF ở `data/landing/legal/`, chưa tự động convert các bài viết markdown từ `data/standardized/news/` sang PDF để upload.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Bổ sung module sinh file PDF tạm từ standardized Markdown để PageIndex có thể index toàn bộ cả legal và news, đồng thời tinh chỉnh tham số $k$ trong RRF qua thực nghiệm Golden Dataset.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Đỗ Nguyễn Ngọc Long

