# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Khắc Giáp — 2A202602950
**Nhóm:** [Tên nhóm]
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding gần như cùng hướng (góc giữa chúng nhỏ, cosine gần 1), tức là mô hình coi hai đoạn văn nói về cùng một ý — dù chúng có thể dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Để duy trì học bổng 100%, sinh viên cần GPA năm học từ 3,2 trở lên."
- Câu B: "Muốn giữ học bổng toàn phần thì điểm trung bình cả năm phải đạt tối thiểu 3.2."
- Tại sao tương đồng: Cùng nói về một điều kiện (ngưỡng GPA để giữ học bổng mức cao nhất), chỉ khác cách diễn đạt ("duy trì" ↔ "giữ", "100%" ↔ "toàn phần").

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Hồ sơ hỗ trợ tài chính phải nộp trước 23:59 ngày 15 hằng tháng."
- Câu B: "Thư viện mở cửa đến 22 giờ vào các ngày trong tuần."
- Tại sao khác: Khác chủ đề hoàn toàn (hạn nộp hồ sơ tài chính vs giờ mở cửa thư viện); điểm chung duy nhất là có mốc thời gian, không đủ để kéo hai vector lại gần nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ so hướng của vector, bỏ qua độ dài; độ dài embedding thường phụ thuộc độ dài/tần suất từ của văn bản chứ không phải nghĩa, nên một đoạn dài và một câu ngắn cùng ý vẫn được cosine đánh giá gần nhau, trong khi khoảng cách Euclid sẽ bị độ dài chênh lệch kéo ra xa. (Với vector đã chuẩn hoá về độ dài 1, hai thước đo cho cùng thứ hạng.)

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* bước nhảy = 500 − 50 = 450; số chunk = ⌈(10000 − 50) / 450⌉ = ⌈9950 / 450⌉ = ⌈22,11⌉
> *Đáp án:* **23 chunks** (kiểm chứng bằng `FixedSizeChunker(500, 50)` trên chuỗi 10,000 ký tự: ra 23 chunk, chunk cuối dài 100 ký tự).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Tăng lên **25 chunks**: ⌈(10000 − 100) / 400⌉ = ⌈24,75⌉ = 25 (bước nhảy giảm từ 450 xuống 400, khớp với `FixedSizeChunker(500, 100)`). Overlap lớn hơn giúp một câu/điều khoản bị cắt ngang ở ranh giới vẫn xuất hiện trọn vẹn trong ít nhất một chunk, nên retrieval ít bị mất ngữ cảnh — đổi lại là nhiều chunk hơn, tốn embedding/bộ nhớ hơn và top-k dễ chứa các chunk trùng lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tách câu bằng `re.split(r"(?<=[.!?])\s+", text)`: lookbehind cắt ở khoảng trắng *sau* dấu `.`/`!`/`?` nên dấu câu vẫn nằm trong câu (split thẳng `[.!?]\s+` sẽ nuốt mất dấu câu), và `\s+` bao cả trường hợp `".\n"`. Sau đó strip, bỏ mảnh rỗng, gom mỗi `max_sentences_per_chunk` câu thành một chunk; text rỗng/chỉ có khoảng trắng trả `[]`. Edge case **chưa xử lý**: chữ viết tắt có dấu chấm + khoảng trắng (`TS. Nguyễn`, `v.v. và`) bị cắt nhầm thành hai câu; số thập phân như `3.2` thì không bị cắt vì sau dấu chấm không có khoảng trắng. Ngoài ra chunker này không giới hạn số ký tự — trên tài liệu quy định duy trì học bổng có chunk dài 672 ký tự.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thử separator theo thứ tự `["\n\n", "\n", ". ", " ", ""]`: tách theo separator lớn nhất có trong text (giữ separator ở cuối mỗi mảnh), rồi **gom** các mảnh liền kề vào buffer cho tới sát `chunk_size`; mảnh nào tự nó vẫn dài hơn `chunk_size` thì đệ quy `_split` với các separator còn lại. Có 3 base case: (1) text đã ≤ `chunk_size` → trả nguyên; (2) hết separator hoặc gặp `""` → cắt cứng theo `chunk_size` (nhờ đó `separators=[]` không crash); (3) separator hiện tại không xuất hiện → chuyển xuống separator kế tiếp. `chunk()` strip và bỏ chunk rỗng ở cuối.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Chỉ dùng in-memory (`self._store` là list record), bỏ hẳn nhánh ChromaDB vì code khởi tạo gốc bật `_use_chroma = True` trước khi có client. `_make_record` embed `content`, **copy** metadata (không sửa dict của người gọi) và `setdefault("doc_id", doc.id)` để `bench.py` có thể đặt `doc_id` = tên file gốc cho các chunk `file#i`. `search` và `search_with_filter` cùng đi qua `_search_records`: embed query, tính `compute_similarity` (cosine đầy đủ — với vector đã chuẩn hoá thì bằng dot product, nhưng an toàn cả khi backend trả vector chưa chuẩn hoá), sắp giảm dần theo score, cắt `top_k`, và bỏ trường `embedding` khỏi kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước** rồi mới xếp hạng: giữ record có mọi cặp key/value trong `metadata_filter` khớp, rồi mới chạy `_search_records` trên tập đó. Nếu lấy top-k trước rồi mới lọc, các slot có thể bị chiếm hết bởi chunk sai audience và trả về rỗng dù store vẫn còn chunk hợp lệ. `metadata_filter=None` coi như không lọc nên cho đúng kết quả của `search`. `delete_document` giữ lại các record có `metadata["doc_id"]` khác `doc_id` (xoá mọi chunk của tài liệu đó) và trả `True` nếu kích thước store giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Ba bước: `store.search(question, top_k)` → dựng prompt → gọi `llm_fn`. Ngữ cảnh được **đánh số** `[1] [2] [3]`, mỗi đoạn kèm nguồn (`source_url`, nếu không có thì `source`/`doc_id`), và prompt yêu cầu model trích số đoạn đã dùng để câu trả lời truy vết được về đúng tài liệu. Prompt có ràng buộc chống bịa: chỉ dùng thông tin trong ngữ cảnh, không đủ thì trả câu "Không tìm thấy thông tin liên quan…". Store rỗng thì trả thẳng câu đó, không gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Embedder: OpenAI `text-embedding-3-small`, điểm tính bằng `compute_similarity` (cosine) trong `src/chunking.py`. Dự đoán được ghi trước khi chạy; quy ước **cao ≥ 0.5**, thấp < 0.5.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Học bổng Sigma Gold trị giá 15 triệu đồng mỗi tháng. | Mỗi tháng sinh viên nhận Sigma Gold được cấp 15 triệu. | cao | 0.830 | ✅ |
| 2 | Sinh viên phải nộp hồ sơ trước ngày 24/06/2026. | Hạn chót gửi giấy tờ đăng ký là 24 tháng 6 năm 2026. | cao | 0.592 | ✅ |
| 3 | Học bổng khuyến khích học tập loại A yêu cầu GPA từ 3.6. | Ký túc xá mở cửa đến 22 giờ mỗi ngày. | thấp | 0.174 | ✅ |
| 4 | Sinh viên được nhận học bổng nếu không trượt môn nào. | Sinh viên bị cắt học bổng nếu trượt một môn. | cao | 0.822 | ✅ |
| 5 | Scholarship recipients must attend the annual award ceremony. | Người nhận học bổng bắt buộc tham dự lễ trao học bổng hằng năm. | cao | 0.366 | ❌ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 5: hai câu cùng nghĩa nhưng khác ngôn ngữ (Anh – Việt) chỉ đạt 0.366, thấp hơn nhiều cặp 2 (cùng ngôn ngữ, gần như không trùng từ nào mà vẫn 0.592) — với model này, ngôn ngữ vẫn chiếm một phần lớn của vector, nên corpus trộn Anh/Việt sẽ truy xuất kém nếu hỏi bằng một ngôn ngữ. Cặp 4 cũng đáng chú ý dù đoán đúng: hai câu mô tả cùng một quy tắc từ hai phía ("không trượt thì được nhận" ↔ "trượt thì bị cắt") đạt 0.822 — embedding nắm **chủ đề** (học bổng + trượt môn) rất tốt nhưng gần như không phân biệt được chiều khẳng định/phủ định, nên nếu hai câu thật sự trái nghĩa thì điểm vẫn sẽ cao. Nói cách khác: cosine đo "đang nói về cùng chuyện gì", chứ không đo "nói điều gì về chuyện đó".

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Cấu hình: chiến lược **heading** (tách theo `##`/`###`, mục dài > 500 ký tự thì cắt recursive và gắn lại tiêu đề vào từng mảnh), corpus nhóm `data/scholarship_final/scholarship` (8 tài liệu → 177 chunk), embedder `text-embedding-3-small`, LLM `gpt-4o-mini`, `top_k=3`. Output đầy đủ: `ket_qua_benchmark.txt` (chạy `python bench.py`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | HB khuyến khích học tập loại A ở Bách khoa Hà Nội yêu cầu GPA và điểm rèn luyện bao nhiêu? | HUST — mục "4. Học bổng khuyến khích học tập": 3 mức A/B/C và điều kiện từng loại | 0.656 | Có — chứa đáp án | "GPA từ 3.6 và điểm rèn luyện từ 90 [1]" — **đúng** |
| 2 | Người nhận học bổng có trách nhiệm gì? *(filter `audience=student`)* | LSTF — "Điều kiện duy trì và tuân thủ", nhưng chỉ là **mảnh bảng hoạt động** (kết nối, lễ trao học bổng) | 0.609 | Một phần — đúng tài liệu, sai mảnh: thiếu CGPA ≥ 2 và "ít nhất 4 dự án" | Liệt kê tham gia hoạt động kết nối và lễ trao học bổng — **đúng nhưng thiếu** |
| 3 | Sinh viên USTH phải nộp hồ sơ Vallet về Phòng CTSV trước ngày nào? | USTH — bảng "IV. Quy trình phối hợp và thời hạn nộp hồ sơ" | 0.705 | Có — chứa dòng 24/06/2026 | "Trước ngày 24/06/2026 [1]" — **đúng** |
| 4 | HB khuyến khích học tập của ĐH Công nghiệp Hà Nội có những mức nào? | HaUI — "2. Học bổng khuyến khích học tập", **nửa đầu** mục (chỉ có mức Xuất sắc) | 0.714 | Một phần — mảnh chứa mức Giỏi/Khá không lọt top-3 (bị chunk HB KKHT của HUST chen vào hạng 2) | Chỉ nêu mức Xuất sắc — **thiếu 2/3 mức** |
| 5 | Học bổng Sigma Gold trị giá bao nhiêu mỗi tháng? | VIASM — "3. Mức học bổng và thời gian cấp" | 0.700 | Có — chứa đáp án | "15 triệu đồng/tháng [1]" — **đúng** |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 nếu chấm theo tài liệu (gold luôn ở top-1), nhưng chỉ **3 / 5** nếu chấm theo nội dung (ngữ cảnh chứa đủ đáp án) — điểm theo thang của `docs/SCORING.md`: **6/10**.

A/B cho câu 2: **không** filter thì top-1 và top-2 là tài liệu `faculty` (UED — học bổng thạc sĩ/tiến sĩ, mục "Trách nhiệm của người nhận học bổng", score 0.720) và agent trả lời "nộp báo cáo nghiên cứu 6 tháng/lần, thanh quyết toán…" — **sai đối tượng**; có filter thì loại được hai chunk đó và agent trả lời đúng đối tượng sinh viên. Filter sửa được lỗi *sai tài liệu*, nhưng không sửa được lỗi *sai mảnh trong đúng tài liệu*.

Phân tích lỗi (câu 2 và 4 cùng một nguyên nhân): mục dài bị cắt thành nhiều mảnh; các mảnh cùng mục có score gần nhau nên mảnh nào lọt top-3 gần như ngẫu nhiên, và mảnh chứa con số cần tìm có thể bị một mục cùng chủ đề của tài liệu khác (HB KKHT của HUST) chen mất chỗ. Đề xuất: truy xuất bằng chunk nhỏ rồi trả về cả mục cha (small-to-big) hoặc nới giới hạn kích thước cho mục có danh sách/bảng để không cắt giữa chừng.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> So sánh 6 chiến lược của nhóm trên cùng `bench.py` cho thấy cả 6 đều đạt 5/5 nếu chỉ kiểm "đúng tài liệu trong top-3", nhưng chấm theo nội dung thì dao động từ 2/5 (sentence, recursive) đến 5/5 (small-to-big) — chấm theo `doc_id` sẽ che mất toàn bộ khác biệt. Chiến lược small-to-big (chunk con ~200 ký tự để tìm, trả về cả mục cha cho agent) đạt 10/10 và sửa đúng hai lỗi của chiến lược heading của tôi, vì nó tách "đơn vị để so khớp" khỏi "đơn vị để đọc".

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
