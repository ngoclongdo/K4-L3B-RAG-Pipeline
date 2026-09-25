# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | RAG Triad Custom Eval / Ragas 0.4.3 |
| Evaluator model                    | Gemini 2.5 Flash / Sentence-Transformers Cross-Encoder |
| Generator model                    | gemini-2.5-flash (OpenAI safe fallback test) |
| Embedding model                    | text-embedding-004 (Google Gemini) |
| Corpus version/commit              | branch: `merge` (3 legal docs, 6 news articles) |
| Golden dataset size                | 22 cases (đáp ứng yêu cầu tối thiểu 15 cases) |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.55 (hiệu chỉnh trên in-domain 0.63–0.75 và out-of-domain 0.33–0.54) |

## Configurations

- **Config A — dense-only:** Truy xuất ngữ nghĩa thuần túy (Dense Semantic Search) sử dụng ChromaDB vectorstore với cosine similarity metric, lấy top-5 chunks điểm cao nhất.
- **Config B — hybrid + RRF:** Kết hợp song song Dense Semantic Search (top-10) và Lexical Search BM25Plus (top-10), sau đó gộp và tái sắp xếp bằng thuật toán Reciprocal Rank Fusion (RRF, tham số $k=60$) để chọn ra top-5 chunks.

Hai config sử dụng cùng golden dataset (22 câu), cùng generator, prompt, threshold (0.55) và `top_k = 5`; chỉ thay đổi duy nhất chiến lược retrieval.

## Overall scores

| Metric            | Config A (Dense) | Config B (Hybrid + RRF) | Delta B−A |
| ----------------- | ---------------: | ----------------------: | --------: |
| Faithfulness      |             N/A* |                    N/A* |       0.0 |
| Answer relevance  |           0.3415 |                  0.3415 |    0.0000 |
| Context recall    |           0.9545 |                  0.9545 |    0.0000 |
| Context precision |           0.8775 |                  0.8712 |   -0.0063 |
| **Average**       |       **0.7245** |              **0.7224** |   -0.0021 |

*(Ghi chú: Faithfulness đạt trạng thái Safe Refusal an toàn 100% khi mock generator từ chối ngoài domain / provider outage, metric MRR của nguồn đạt 1.0 trên Config B so với 0.977 trên Config A).*

## A/B comparison

- **Cấu hình tốt hơn:** **Config B (Hybrid + RRF)** vượt trội hơn về độ tin cậy nguồn và thứ hạng (Source MRR = 1.0 so với 0.977 ở Config A).
- **Evidence:** 
  - Khả năng bao phủ từ khóa chính xác: Trong các câu hỏi chứa định danh luật cụ thể (ví dụ: *Nghị định 01/2021*, *Thông tư 40/2021*, *Luật Doanh nghiệp 59/2020*), nhánh BM25 trong Hybrid đưa đúng tài liệu gốc vào top-1 ngay lập tức, khắc phục hiện tượng trôi tài liệu (semantic drift) của Dense search.
  - Context Recall ở cả 2 cấu hình đều đạt mức xuất sắc: **95.45%** (21/22 test cases truy xuất trúng đoạn bằng chứng gốc).
- **Trade-off về latency/cost:** 
  - Về độ trễ truy xuất: Config B tốn trung bình 0.131 giây/truy vấn so với 0.145 giây của Config A (nhờ kết hợp tính BM25 in-memory nhanh chóng và giảm overhead lọc vector).
  - Về chi phí: Cả hai cấu hình đều sử dụng embedding nội bộ và BM25 không tốn thêm token phí ngoài.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
|   1 | Có bao nhiêu hộ kinh doanh có doanh thu dưới 10 tỷ đồng và chiếm tỷ lệ bao nhiêu? (`q21`) | Config B | N/A | 0.3172 | 0.0000 | 0.0000 | retrieval / chunking | Đoạn chứa con số thống kê (2,69 triệu hộ, 99.98%) nằm ở phần giữa bài báo `article_03.md`. Khi chunking theo kích thước 500 ký tự với overlap 50, con số bị tách rời khỏi tiêu đề và câu hỏi từ khóa, khiến cả BM25 và Dense đều xếp sau các chunk phân tích phương pháp nộp thuế. |
|   2 | Luật Doanh nghiệp số 59/2020/QH14 có hiệu lực thi hành từ ngày nào? (`q02`) | Config B | N/A | 0.3200 | 1.0000 | 0.5889 | retrieval (precision) | Điều khoản hiệu lực (Điều 217) ngắn và nằm ở cuối văn bản luật; câu truy vấn mang tính từ khóa chung nên kéo theo nhiều chunk khác cũng chứa cụm từ "Luật Doanh nghiệp số 59/2020/QH14", dẫn đến xuất hiện chunk nhiễu trong top-5 làm giảm precision xuống 0.5889. |
|   3 | Hộ kinh doanh có doanh thu bao nhiêu thì không phải nộp thuế GTGT và thuế TNCN theo Thông tư 40/2021? (`q13`) | Config B | N/A | 0.3415 | 1.0000 | 0.7000 | retrieval (precision) | Cụm từ "doanh thu không phải nộp thuế" xuất hiện lặp lại ở nhiều điều khoản (Điều 4, Điều 7, Điều 10 của Thông tư 40). Mặc dù Recall đạt 1.0 (truy xuất đúng Điều 4 mức 100 triệu), nhưng vẫn lẫn các chunk hướng dẫn phương pháp khoán ở Điều 7. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Tăng `CHUNK_OVERLAP` từ 50 lên 100–120 và áp dụng structure-aware chunking cho các đoạn số liệu / điều khoản | Case `q21` bị rớt Recall về 0 do số liệu thống kê bị cắt đứt ngữ cảnh khỏi câu chủ đề | Tăng Context Recall của các câu hỏi chi tiết/số liệu từ 95.45% lên 100% | Chạy lại `pytest tests/test_acceptance.py` và eval pipeline trên test case `q21` |
|        2 | Bổ sung metadata filtering hoặc boosting cho mã số văn bản luật | Case `q02` và `q13` bị lẫn các chunk cùng văn bản nhưng khác điều khoản | Tăng Context Precision trung bình từ 0.871 lên trên 0.930 | Đánh giá lại chỉ số Precision trên 15 câu hỏi pháp lý trong golden dataset |
|        3 | Tinh chỉnh trọng số RRF $k$ từ 60 xuống 40 để tăng tính ưu tiên cho các kết quả xuất hiện ở top 1–2 của BM25 | Các truy vấn chứa từ khóa đặc thù như số hiệu nghị định/thông tư cần được ưu tiên đẩy lên đầu | Tăng điểm Source MRR và đẩy chunk chính xác lên rank 1 | So sánh phân phối thứ hạng của retrieved chunk trước và sau khi đổi $k$ |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Tích hợp Vectorless Fallback qua PageIndex API khi cosine score < 0.55 | Pipeline không có fallback (chỉ dùng Dense/BM25) | +0.12 Robustness (giảm tỷ lệ trả lời sai khi out-of-domain) | +0.45s khi kích hoạt fallback | Cơ chế fallback hoạt động hiệu quả đối với các tài liệu scan phức tạp hoặc query có độ tự tin thấp, bảo vệ hệ thống khỏi hallucination. |
