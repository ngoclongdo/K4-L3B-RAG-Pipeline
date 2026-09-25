# Hướng Dẫn & Quy Chuẩn RAG Pipeline (Context)

Tài liệu này tổng hợp toàn bộ quy trình, hợp đồng kỹ thuật (contracts), yêu cầu kiểm thử và tiêu chuẩn đánh giá cho hệ thống RAG Pipeline theo 5 giai đoạn (phases).

---

## 1. Chuẩn Bị Dữ Liệu (Corpus & Data Processing)

### Mục tiêu & Yêu cầu dữ liệu
* **Chủ đề**: Chọn 1 chủ đề cụ thể, ổn định (không thay đổi quá nhanh, không chứa dữ liệu cá nhân, có bản quyền sử dụng).
* **Tài liệu pháp lý / chính sách (`legal`)**: Tối thiểu 3 tài liệu định dạng `PDF`, `DOC` hoặc `DOCX`.
* **Bài viết / tin tức (`news`)**: Tối thiểu 5 bài viết / URL công khai. Nguồn phải có tên, URL và nội dung kiểm chứng được.

### Cấu trúc thư mục dữ liệu
* **Thô (Landing)**: `data/landing/legal/` và `data/landing/news/`
* **Chuẩn hóa (Standardized)**: `data/standardized/legal/` và `data/standardized/news/`

### Quy cách dữ liệu chuẩn hóa
* **Bài viết (News JSON)**: Bắt buộc chứa các trường `url`, `title`, `date_crawled`, `content_markdown`.
* **Tài liệu chính sách (Legal Markdown)**: Chuyển đổi sang file định dạng `.md` giữ nguyên cấu trúc phân cấp.

### Quy trình thực hiện
1. Tải tối thiểu 3 tài liệu vào `data/landing/legal/`.
2. Khai báo ít nhất 5 URL vào `ARTICLE_URLS` trong [src/task2_crawl_news.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task2_crawl_news.py), hoàn thiện hàm `crawl_article()` (sử dụng Crawl4AI, Firecrawl,...).
3. Hoàn thiện [src/task3_convert_markdown.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task3_convert_markdown.py) (sử dụng MarkItDown hoặc công cụ tương đương) để chuẩn hóa sang Markdown.
4. Chạy kiểm tra acceptance test:
   ```bash
   python -m src.task1_collect_legal_docs
   python -m src.task2_crawl_news
   python -m src.task3_convert_markdown
   pytest tests/test_acceptance.py -q
   ```

> [!NOTE]
> **Checkpoint Dữ liệu:**
> - [x] Tối thiểu 3 file chính sách hợp lệ.
> - [x] Tối thiểu 5 file JSON bài viết đầy đủ metadata.
> - [x] Cả hai thư mục `standardized/legal` và `standardized/news` đều chứa file Markdown.
> - [x] Đối chiếu được mẫu nội dung với nguồn công khai.
> - [x] Không chứa dữ liệu cá nhân (PII) hoặc tài liệu vi phạm bản quyền.

---

## 2. Chunking, Embedding & Hai Nhánh Tìm Kiếm (Retrieval)

### Data Contracts (Quy chuẩn dữ liệu)
* **Document**: `{id, content, metadata}`
* **Chunk**: Bổ sung `chunk_index` so với Document.
* **SearchResult**: Bổ sung `score`, `retrieval_method`.

### Chiến lược Chunking & Indexing
* **Cấu hình mặc định (Starter)**:
  * `CHUNK_SIZE = 500`
  * `CHUNK_OVERLAP = 50`
  * `CHUNKING_METHOD = "recursive"`
* **Yêu cầu quan trọng**:
  * Giữ mối liên kết giữa chunk và tài liệu gốc.
  * Sử dụng ID ổn định kèm cơ chế **upsert** để tránh trùng lặp dữ liệu khi index lại.
  * Hàm `embed_texts()` dùng chung cho cả Task 4 (embed corpus) và Task 5 (embed query) để đồng bộ model và dimension.

### Hai đường tìm kiếm song song
* **Dense Retrieval (`retrieval_method="dense"`)**:
  * Tìm kiếm theo ngữ nghĩa dựa trên ChromaDB vectorstore.
  * Đổi cosine distance sang cosine similarity trước khi sắp xếp giảm dần.
* **BM25 / Lexical Search (`retrieval_method="bm25"`)**:
  * Tìm kiếm theo từ khóa, mã số hiệu văn bản, tên riêng.
  * Sắp xếp điểm số BM25 giảm dần.

### Quy trình thực hiện
1. Hoàn thiện [src/task4_chunking_indexing.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task4_chunking_indexing.py): `load_documents()`, `chunk_documents()`, `embed_texts()`, `embed_chunks()`, `get_collection()`, `index_to_vectorstore()`.
2. Hoàn thiện `semantic_search()` trong [src/task5_semantic_search.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task5_semantic_search.py).
3. Hoàn thiện `build_bm25_index()` và `lexical_search()` trong [src/task6_lexical_search.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task6_lexical_search.py).
4. Kiểm thử contract:
   ```bash
   python -m src.task4_chunking_indexing
   python -m src.task5_semantic_search
   python -m src.task6_lexical_search
   pytest tests/test_contracts.py -q
   ```

---

## 3. Hợp Nhất Thứ Hạng (RRF) & Thiết Kế Fallback

### Thuật toán Reciprocal Rank Fusion (RRF)
* **Lý do**: Dense similarity và BM25 score không cùng thang đo, không được cộng gộp trực tiếp.
* **Công thức**:
  $$\text{Score}_{\text{RRF}}(d) = \sum_{m \in M} \frac{1}{k + \text{rank}_m(d)}$$
  *(với $\text{rank} \ge 1$)*
* **Quy tắc hàm `rerank_rrf()`**:
  * Nhận nhiều danh sách đã rank, gộp theo `id`.
  * **Deep copy** item trước khi gán lại score để tránh mutate kết quả gốc.
  * Đặt `retrieval_method = "hybrid"`, sắp xếp giảm dần, giới hạn `top_k`, không trùng lặp `id`.

### Cơ chế Fallback
* **Độ tự tin**: Dựa trên **best cosine score gốc của Dense search**, tuyệt đối không dùng điểm RRF.
* **Quy trình fallback**:
  * Nếu `dense_score < SCORE_THRESHOLD`: thử gọi `pageindex_search()` từ [src/task8_pageindex_vectorless.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task8_pageindex_vectorless.py).
  * Nếu provider fallback gặp lỗi / timeout: Pipeline **không được crash**, phải giữ lại kết quả hybrid hiện có hoặc chuyển sang safe refusal ở pha sinh phản hồi.

### Quy trình thực hiện
1. Hoàn thiện `rerank_rrf()` trong [src/task7_reranking.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task7_reranking.py).
2. Hoàn thiện fallback vectorless trong [src/task8_pageindex_vectorless.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task8_pageindex_vectorless.py) (nếu áp dụng PageIndex).
3. Hoàn thiện hàm `retrieve()` trong [src/task9_retrieval_pipeline.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task9_retrieval_pipeline.py).
4. Kiểm thử:
   ```bash
   python -m src.task7_reranking
   pytest tests/test_contracts.py -q
   ```

---

## 4. Sinh Câu Trả Lời Có Trích Dẫn & Giao Diện (Generation & UI)

### Tối ưu hóa Context & Sinh phản hồi
* **`reorder_for_llm()`**: Đổi thứ tự chunk để tránh hiện tượng thông tin quan trọng bị "lost in the middle" (không được làm mất/sửa ID).
* **`format_context()`**: Gắn kèm `title` và `source` vào từng đoạn context.
* **`call_llm()`**: Phân phối theo cấu hình `LLM_PROVIDER` (`openai`, `gemini`, `anthropic`). Giữ output dạng chuỗi text thuần.
* **Contract `GenerationResult`**:
  * `answer`: Nội dung câu trả lời.
  * `sources`: Danh sách `SearchResult` được trích dẫn.
  * `retrieval_source`: `"hybrid"`, `"pageindex"`, hoặc `"none"`.
* **Safe Refusal**: Khi không đủ bằng chứng hoặc câu hỏi ngoài phạm vi domain, hệ thống phải từ chối lịch sự, trả về `sources=[]` và `retrieval_source="none"`.

### Giao diện Streamlit (`app.py`)
* Cho phép nhập câu hỏi (`query`) và chỉnh `top_k`.
* Hiển thị câu trả lời (`answer`), nguồn (`sources`), phương thức truy xuất (`retrieval_method`) và điểm số (`score`).
* Citation phải map chính xác về `SearchResult` trong `sources`.
* Lưu lịch sử hội thoại vào `st.session_state` với đầy đủ metadata để render lại.

### Quy trình thực hiện
1. Hoàn thiện các hàm trong [src/task10_generation.py](file:///d:/VinUni/day8/K4-L3B-RAG-Pipeline/src/task10_generation.py).
2. Kiểm tra contract test và khởi chạy giao diện:
   ```bash
   pytest tests/test_contracts.py -q
   streamlit run app.py
   ```

---

## 5. Đánh Giá A/B & Phân Tích Lỗi (Evaluation)

### Thiết kế thử nghiệm A/B
* **Config A**: Baseline (Dense-only retrieval).
* **Config B**: Hybrid (Dense + BM25 + RRF).
* **Nguyên tắc kiểm soát biến**: Giữ nguyên toàn bộ các thành phần khác (Golden dataset, model generator, evaluator, prompt, top_k, threshold).

### Bộ dữ liệu chuẩn (Golden Dataset)
* Tệp `group_project/evaluation/golden_dataset.json` tối thiểu **15 test cases**.
* Mỗi test case gồm 3 trường: `question`, `expected_answer`, `expected_context`.
* Bắt buộc bám sát corpus thực tế; phân bổ các câu hỏi dạng từ khóa cụ thể, câu hỏi tương đồng ngữ nghĩa, và câu hỏi dễ nhầm lẫn.

### Bộ 4 chỉ số đo lường (RAG Triad & Precision)
1. **Context Recall**: Khả năng truy xuất đầy đủ bằng chứng cần thiết.
2. **Context Precision**: Mức độ tập trung của các đoạn trích (ít nhiễu).
3. **Faithfulness**: Câu trả lời có trung thực và bám sát context không.
4. **Answer Relevance**: Câu trả lời có giải quyết đúng trọng tâm câu hỏi không.

### Phân tích lỗi theo tầng (Failure Analysis)
* *Recall / Precision thấp* $\rightarrow$ Lỗi ở khâu Corpus, Chunking hoặc Retrieval.
* *Faithfulness thấp (dù Context đúng)* $\rightarrow$ Lỗi ở Prompt hoặc Generator.
* *Relevance thấp* $\rightarrow$ Lỗi phối hợp giữa Retrieval và Generation.

### Yêu cầu báo cáo (`RESULT.md`)
* Bảng điểm tổng hợp của 2 cấu hình và giá trị chênh lệch ($\Delta = B - A$).
* Phân tích sâu ít nhất **3 worst performers** kèm Root Cause cụ thể.
* Đề xuất cải tiến (Recommendation) có thể kiểm chứng lại bằng thực nghiệm.

> [!NOTE]
> **Checkpoint Evaluation:**
> - [x] Golden dataset có tối thiểu 15 cases bám sát corpus.
> - [x] Hai cấu hình chỉ khác nhau duy nhất về chiến lược retrieval.
> - [x] Báo cáo đầy đủ 4 metrics và delta $\Delta(B - A)$.
> - [x] 3 case kém nhất có phân tích nguyên nhân gốc rễ (root cause).
> - [x] Có khuyến nghị kiểm chứng kèm phương pháp chạy lại.
