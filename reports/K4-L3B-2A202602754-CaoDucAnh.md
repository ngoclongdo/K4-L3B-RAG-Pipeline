# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: Cao Đức Anh
- Mã học viên: 2A202602754
- Nhóm: Kocoten
- Repository/branch: https://github.com/ngoclongdo/K4-L3B-RAG-Pipeline/tree/ducanh

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 9 — Retrieval pipeline & Fallback | Xây dựng pipeline `retrieve()` hoàn chỉnh: kết hợp song song `semantic_search` và `lexical_search` (BM25), fuse thứ hạng qua `rerank_rrf()` đúng một lần; kiểm soát độ tự tin bằng best cosine score gốc của dense retrieval, kích hoạt fallback sang `pageindex_search` khi score dưới threshold; bọc cơ chế chống crash khi fallback lỗi. | `src/task9_retrieval_pipeline.py` | Done |
| Task 10 — Generation có citation & Safe refusal | Xây dựng hàm `generate_with_citation()` và `generate_from_chunks()`: thuật toán `reorder_for_llm` giảm lost-in-the-middle, hàm `format_context` chuẩn hóa kèm title và source, cơ chế multi-provider (`OpenAI`, `Gemini`, `Anthropic`), hàm `extract_citations` trích xuất `[n]` map về `sources`, và safe refusal khi context không đủ bằng chứng hoặc provider lỗi. | `src/task10_generation.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

---

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Sử dụng best cosine similarity score gốc của Dense search để quyết định kích hoạt fallback PageIndex, tuyệt đối không dùng điểm RRF.  
   **Lý do/evidence:** Điểm RRF chỉ đại diện cho thứ hạng tương đối phụ thuộc vào số lượng và độ dài danh sách fusion, không phản ánh độ tương đồng ngữ nghĩa thực tế. Cosine score phản ánh chính xác mức độ liên quan ngữ nghĩa giữa câu hỏi và corpus; ngưỡng `SCORE_THRESHOLD = 0.55` được hiệu chỉnh qua các query in-domain và out-of-domain.  
   **Trade-off:** Cần lưu giữ và trích xuất điểm dense score gốc trước khi thực hiện rerank.

2. **Quyết định:** Áp dụng kỹ thuật `reorder_for_llm()` (sắp xếp dạng U-shaped / Lost-in-the-middle mitigation) và ép buộc citation theo chỉ số tài liệu `[n]`.  
   **Lý do/evidence:** Các mô hình ngôn ngữ lớn (LLM) thường chú ý tốt nhất ở phần đầu và phần cuối context, dễ bỏ quên thông tin quan trọng ở đoạn giữa. Việc đảo thứ tự các chunk có rank cao ra hai đầu context giúp tăng độ chính xác và khả năng trích dẫn đúng nguồn.  
   **Trade-off:** Cần gắn chỉ số nhận diện `citation` vào metadata trước khi reorder để citation trong câu trả lời vẫn map chính xác về vị trí ban đầu trong `sources`.

---

## Kiểm thử và kết quả

- **Test hoặc query tôi đã dùng:**  
  - Chạy toàn bộ test contract cho Task 9 và Task 10 trong `tests/test_contracts.py`:
    `pytest tests/test_contracts.py -k "test_retrieve or test_reorder or test_generation" -v`
  - Thử nghiệm query đúng domain ("Ai không có quyền thành lập doanh nghiệp?") và query ngoài domain ("Công thức nấu phở bò?") để kiểm tra safe refusal.
- **Kết quả trước/sau nếu có:**  
  - Trước: Task 9 và Task 10 ném `NotImplementedError`, pipeline chưa kết nối end-to-end.  
  - Sau: Toàn bộ contract tests đều **PASSED 100%**. Pipeline phản hồi câu trả lời chuẩn xác kèm trích dẫn `[1]` cho câu hỏi trong domain, và từ chối an toàn trả về đúng câu quy định với câu hỏi ngoài domain.
- **Lỗi đã phát hiện và cách xử lý:**  
  - Khi provider LLM gặp sự cố mạng hoặc timeout, hàm generation có nguy cơ làm gián đoạn chatbot; đã bổ sung khối `try/except` trả về safe refusal và log cảnh báo lỗi.  
  - Đảm bảo regex `extract_citations` chỉ nhận các số `[n]` nằm trong khoảng `1 <= n <= len(sources)` để tránh hallucination citation.

---

## Điều còn hạn chế

- **Một hạn chế cụ thể của phần tôi làm:** Prompt generation hiện tại được tối ưu dạng zero-shot; khi context có nhiều điều khoản phức tạp, đôi khi LLM gộp câu trả lời quá ngắn.  
- **Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:** Bổ sung few-shot examples vào system prompt để chuẩn hóa hơn nữa phong cách trích dẫn pháp lý chuyên nghiệp.

---

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Cao Đức Anh
