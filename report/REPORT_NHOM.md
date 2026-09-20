Báo Cáo Nhóm — Lab 7: Embedding & Vector Store
Nhóm: L3A — Nhóm Học Bổng Đại Học
Thành viên:
Nguyễn Việt Hoàng Hải — 2A202602967
Nguyễn Thị Minh Khánh — 2A202602546
Nguyễn Khắc Giáp — 2A202602950
Nguyễn Quang Huy — 2A202602421
Lại Bá Quân — 2A202602495
Thiều Quang Vinh — 2A202602877
Ngày: 20/09/2026
> **Nộp 1 bản / nhóm.** Phần cá nhân nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.
Tổng điểm phần nhóm: 40 = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).
---
1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)
Chủ đề (Domain) & Lý Do Chọn
Chủ đề: Học bổng và chính sách hỗ trợ tài chính cho người học tại các trường đại học Việt Nam.
Tại sao nhóm chọn chủ đề này?
> Đây là thông tin sinh viên tra cứu thường xuyên nhưng nằm rải rác ở hàng chục cổng thông tin khác nhau, mỗi trường một định dạng — đúng bài toán RAG giải quyết tốt. Chủ đề giàu số liệu kiểm chứng được (ngưỡng GPA, mức tiền, số suất, hạn nộp) nên gold answer trích thẳng từ nguồn, không phải suy đoán. Nhóm cũng cố ý đưa vào 2 tài liệu dành cho đối tượng sau đại học / giảng viên để `search_with_filter()` có dữ liệu thật mà lọc.
Danh sách tài liệu (Data Inventory)
#	Tên tài liệu	Nguồn (Source URL)	Ngày lấy / Phiên bản	Số ký tự	Metadata đã gán
1	Học bổng và hỗ trợ tài chính cho sinh viên - Đại học...<br>`haui-financial-aid-scholarships.md`	https://www.haui.edu.vn/vn/hoc-bong-hoc-phi/ho-tro-tai-chinh-va-hoc-bong-danh-cho-sinh-vien-haui/68191	2026-09-19 / `not-stated`	8,678	`audience=student`, `category=scholarships`, `language=vi`
2	Hỗ trợ tài chính cho sinh viên - Đại học Bách khoa H...<br>`hust-financial-aid-for-students.md`	https://ts.hust.edu.vn/tin-tuc/ho-tro-tai-chinh-cho-sinh-vien	2026-09-19 / `2025`	2,698	`audience=student`, `category=scholarships`, `language=vi`
3	Học bổng Thạc sĩ nghiên cứu ĐHBKHN - Đại học Bách kh...<br>`hust-postgrad-research-scholarships.md`	https://ts.hust.edu.vn/tin-tuc/hoc-bong-thac-s-nghien-cuu-dhbkhn	2026-09-19 / `not-stated`	2,771	`audience=faculty`, `category=scholarships`, `language=vi`
4	Chương trình học bổng Jensen Huang năm 2025<br>`iuoss-jensen-huang-scholarship.md`	https://iuoss.com/chuong-trinh-hoc-bong-jensen-huang-nam-2025/	2026-09-19 / `2025`	6,825	`audience=student`, `category=scholarships`, `language=vi`
5	Học bổng Đinh Thiện Lý - Quỹ Hỗ trợ Cộng đồng Lawren...<br>`lstf-dinh-thien-ly-scholarship.md`	https://www.lstf.org.vn/vi/linh-vuc/giao-duc/hoc-bong-dinh-thien-ly/	2026-09-19 / `not-stated`	13,862	`audience=student`, `category=scholarships`, `language=vi`
6	Chương trình học bổng đào tạo thạc sĩ, tiến sĩ trong...<br>`ued-postgrad-scholarships.md`	https://tt.ued.udn.vn/hoc-bong-thac-si-tien-si-trong-nuoc/	2026-09-19 / `2022`	6,519	`audience=faculty`, `category=scholarships`, `language=vi`
7	Thông báo triển khai chương trình học bổng Vallet nă...<br>`usth-vallet-scholarship-2026.md`	https://usth.edu.vn/thong-bao-trien-khai-chuong-trinh-hoc-bong-vallet-nam-2026-danh-cho-sinh-vien-khu-vuc-mien-bac-31432/	2026-09-19 / `2026`	6,544	`audience=student`, `category=scholarships`, `language=vi`
8	Học bổng Sigma Gold năm học 2026-2027 cho sinh viên ...<br>`viasm-sigma-gold-scholarship.md`	https://viasm.edu.vn/hoat-dong-khoa-hoc/tin-tuc/chi-tiet/hoc-bong-sigma-gold-nam-hoc-2026-2027-cho-sinh-vien-nganh-toan	2026-09-19 / `2026-2027`	3,681	`audience=student`, `category=scholarships`, `language=vi`
Tổng: 8 tài liệu, 51.578 ký tự. Phân bố `audience`: `student` (6), `faculty` (2).
Kiểm kê đối chiếu 1-1 tại `data/scholarship/sources.csv`.
Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):
[x] Corpus chỉ chứa nguồn công khai/được phép dùng, không có dữ liệu cá nhân hay tài liệu nội bộ — toàn bộ là cổng tuyển sinh / quỹ học bổng công khai, `license_or_permission=public-source`.
[x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` — đã kiểm tự động, 0 lỗi. Nguồn không nêu phiên bản thì ghi `not-stated`, không bịa số hiệu.
Cấu trúc Metadata (Metadata Schema)
Trường metadata	Kiểu	Ví dụ giá trị	Tại sao hữu ích cho truy xuất?
`doc_id`	string	`viasm-sigma-gold-scholarship`	Khoá ổn định, trùng tên file; gom chunk về tài liệu gốc và phục vụ `delete_document()`.
`audience`	enum	`student` / `faculty`	Trường lọc chính. Câu 5 của nhóm chứng minh: không lọc thì tài liệu `faculty` chen vào top-3 và đẩy tài liệu `student` đúng ra ngoài.
`category`	string	`scholarships`	Phân nhóm chủ đề, dự phòng khi corpus mở rộng sang thư viện / ký túc xá.
`language`	string	`vi`	Corpus hiện thuần tiếng Việt; giữ trường này để mở rộng sang tài liệu tiếng Anh.
`document_version`	string	`2026-2027`, `not-stated`	Phân biệt quy định còn hiệu lực với bản cũ — corpus có tài liệu từ 2019 và 2022.
`source_url`	string	`https://viasm.edu.vn/...`	Truy vết gốc để kiểm chứng gold answer và trích dẫn trong câu trả lời.
Ghi chú chất lượng dữ liệu
Nhóm đã rà soát và vá 3 lỗi kỹ thuật trong corpus dùng chung:
Lỗi	Ảnh hưởng	Đã xử lý
`sources.csv` có title chứa dấu phẩy chưa bọc ngoặc	Dòng vỡ thành 10 trường thay vì 7; `csv.DictReader` đọc `document_version` thành `" Đại học Đà Nẵng"`	Dựng lại bằng `csv.DictWriter`, tự bọc ngoặc
Email bị Cloudflare che ở 2 tài liệu	Hiện thành `[email protected]`, mất địa chỉ liên hệ thật	Giải ngược hash, khôi phục `cim@hcmiu.edu.vn`, `nbhan@hcmiu.edu.vn`, `education@lstf.org.vn`
Widget chia sẻ mạng xã hội sót trong tài liệu USTH	Rác web lọt vào chunk, làm nhiễu embedding	Đã xoá
Hạn chế đã biết: 2 tài liệu lỗi thời — `hust-postgrad-research-scholarships` (đăng 26-09-2019) và `ued-postgrad-scholarships` (hạn nộp 05–06/2022). Nhóm giữ lại vì đây đúng là 2 tài liệu `audience=faculty` tạo nên bẫy metadata, nhưng gold answer từ 2 tài liệu này không phản ánh quy định hiện hành.
---
2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)
Phân tích đường cơ sở (Baseline Analysis)
Chạy `ChunkingStrategyComparator().compare(text, chunk_size=350)` trên 3 tài liệu đại diện:
Tài liệu	Chiến lược	Số chunk	Độ dài TB	Giữ được ngữ cảnh không?
`hust-financial-aid`<br>(2.698 ký tự)	`fixed_size`	9	344	Trung bình — cắt giữa bảng mức A/B/C
	`by_sentences`	4	674	Tốt — mỗi chunk trọn một mục chính sách
	`recursive`	11	244	Tốt — bám ranh giới đoạn
`haui-financial-aid`<br>(8.678 ký tự)	`fixed_size`	29	348	Kém — tài liệu dài, dễ cắt đứt số tiền khỏi tên ngành
	`by_sentences`	25	345	Trung bình
	`recursive`	34	254	Tốt nhất trong 3
`viasm-sigma-gold`<br>(3.681 ký tự)	`fixed_size`	13	329	Trung bình
	`by_sentences`	7	524	Tốt
	`recursive`	16	229	Tốt
Nhận xét: `recursive` luôn sinh nhiều chunk nhỏ nhất (229–254 ký tự) vì bám ranh giới đoạn và dòng. `by_sentences` biến động mạnh theo văn phong tài liệu (674 ký tự ở HUST nhưng 345 ở HaUI) vì phụ thuộc độ dài câu. `fixed_size` ổn định về kích thước nhưng là loại duy nhất cắt ngang giữa một con số và ngữ cảnh định danh nó.
Chiến lược của từng thành viên
Thành viên 1 — Nguyễn Việt Hoàng Hải
Loại chiến lược: Custom — `HeadingChunker` (đáp ứng yêu cầu riêng của L3A: chunking theo tiêu đề/mục)
Mô tả & lý do chọn: Tài liệu quy định học bổng có cấu trúc phân tầng rõ theo heading Markdown. `HeadingChunker` bóc tách theo từng heading; nếu một mục vượt `max_chunk_size=600` thì dùng `RecursiveChunker` chia nhỏ và gắn lại tiêu đề heading cha vào đầu mỗi mảnh con. Nhờ đó chunk con không bao giờ mất ngữ cảnh "đây là quy định về mục gì".
Thành viên 2 — Nguyễn Thị Minh Khánh
Loại chiến lược: `FixedSizeChunker`
Mô tả & lý do chọn: Chọn làm đường cơ sở để đo xem cắt "mù" theo độ dài cố định gây thiệt hại bao nhiêu so với các chiến lược bám cấu trúc. Kết luận từ phân tích lỗi: với câu hỏi tra số liệu, `FixedSizeChunker` rất dễ cắt đôi đoạn ngay giữa con số — chunk 1 có chữ "Vi mạch bán dẫn" nhưng mất số tiền, chunk 2 có số tiền nhưng mất chủ đề, khiến cả hai cùng tụt hạng.
Thành viên 3 — Thiều Quang Vinh
Loại chiến lược: `RecursiveChunker(chunk_size=350)`
Mô tả & lý do chọn: Ưu tiên phân cách lớn trước, đồng thời gom các mảnh vụn liền kề tới sát ngưỡng để tránh sinh chunk vài ký tự. Chạy với mô hình local thật: embedding `BAAI/bge-m3`, LLM `Qwen2.5-1.5B-Instruct`, cho 228 chunk trên 8 tài liệu.
Thành viên 4 — Lại Bá Quân
Loại chiến lược: `HeadingChunker`
Mô tả & lý do chọn: Cùng hướng với Hải nhưng khác ở khâu đánh dấu: mỗi chunk con được gắn tiền tố `[Tiêu đề]` ngay trong nội dung, nên LLM nhìn thấy ngữ cảnh mục ngay trong văn bản chứ không chỉ trong metadata. Chạy với API thật của Google Gemini (`gemini-embedding-001` cho nhúng, `gemini-3.6-flash` cho sinh câu trả lời), cho 166 chunk trên 8 tài liệu. Đây là lần chạy có chất lượng truy xuất cao nhất nhóm: 9/10.
Thành viên 5 — Nguyễn Khắc Giáp
Loại chiến lược: `heading` (tách theo `##`/`###`, mục dài trên 500 ký tự thì cắt recursive rồi gắn lại tiêu đề vào từng mảnh)
Mô tả & lý do chọn: Cùng họ với `HeadingChunker` của Hải và Bá Quân nhưng ngưỡng cắt khác. Chạy với API OpenAI: embedding `text-embedding-3-small`, LLM `gpt-4o-mini`, cho 177 chunk trên 8 tài liệu. Đóng góp riêng của Giáp là cách chấm hai thang: cùng một lần chạy, chấm theo tài liệu thì được 5/5, nhưng chấm theo nội dung (ngữ cảnh có chứa đủ đáp án không) thì chỉ còn 3/5. Bạn tự hạ điểm mình xuống 6/10 theo thang nghiêm hơn.
Thành viên 6 — Nguyễn Quang Huy
Loại chiến lược: Không chọn một chiến lược riêng — nhận vai trò chạy đối chứng có kiểm soát.
Mô tả & lý do chọn: Sau khi thấy mỗi thành viên dùng một bộ nhúng khác nhau, nhóm cần một phép đo giữ nguyên mọi biến số ngoại trừ chiến lược chunking. Huy chạy cả 3 chiến lược trên cùng bộ 5 câu hỏi chung, rồi lặp lại toàn bộ với 2 bộ nhúng (`paraphrase-multilingual-MiniLM-L12-v2` và TF-IDF từ vựng tự cài), đồng thời tự thêm chỉ số độ phủ đáp án ở mức chunk. Công cụ: `benchmark/run_comparison.py`; kết quả: `benchmark/RESULTS.md`.
So Sánh Giữa Các Thành Viên
Thành viên	Chiến lược	Bộ nhúng đã dùng	Top-3 hit	Điểm truy xuất (/10)	Điểm mạnh	Điểm yếu
Hải	`HeadingChunker`	MockEmbedder	2/5	4	Chunk luôn mang ngữ cảnh heading cha	Chưa đo được đúng năng lực vì bộ nhúng giả
Khánh	`FixedSizeChunker`	MockEmbedder	0/5	0	Đường cơ sở rõ ràng, phân tích lỗi sắc	Cắt ngang số liệu; bộ nhúng giả
Bá Quân	`HeadingChunker`	Gemini API	5/5	9	Điểm cao nhất nhóm; tiền tố `[Tiêu đề]` giúp LLM trích dẫn đúng đến từng con số	Phụ thuộc API trả phí, khó tái lập nếu hết quota
Vinh	`RecursiveChunker(350)`	`BAAI/bge-m3`	5/5	7	Chạy mô hình local thật, có cả LLM sinh câu trả lời	Top-1 sai ở 1/5 câu; 3/5 câu trả lời chưa đạt ngưỡng 0.80
Giáp	`heading` (ngưỡng 500)	OpenAI `text-embedding-3-small`	5/5	6	Tự chấm hai thang, phát hiện lỗi "đúng tài liệu, sai mảnh"; đề xuất small-to-big	Tự hạ điểm theo thang nghiêm nên khó so trực tiếp với các bạn chấm thang lỏng
Huy	(đối chứng cả 3)	MiniLM + TF-IDF	4/5	9	Phép đo duy nhất cố định được biến số; thêm chỉ số phủ đáp án	Chưa nối LLM nên không chấm được vế câu trả lời
> **Cảnh báo phương pháp — đọc kỹ trước khi so sánh các dòng trên.**
> Năm thành viên **không chạy cùng một bộ nhúng**: Hải và Khánh dùng `MockEmbedder` (băm MD5, không mang ngữ nghĩa), Vinh dùng `BAAI/bge-m3`, Bá Quân dùng Gemini API, Huy dùng MiniLM và TF-IDF. Vì vậy chênh lệch 0/5 — 2/5 — 5/5 **phản ánh chủ yếu sự khác nhau của bộ nhúng, không phải của chiến lược chunking**. Bằng chứng rõ nhất: Hải và Bá Quân dùng **cùng một chiến lược `HeadingChunker`** nhưng ra 2/5 và 5/5, chênh nhau chỉ vì một bên chạy MockEmbedder còn bên kia chạy Gemini.
>
> Phép đo của Huy được thiết kế đúng để khắc phục điều này — cố định bộ nhúng, chỉ đổi chiến lược. Kết quả: **cả ba chiến lược đều đạt Hit@3 80%** (MiniLM), khác biệt thật chỉ lộ ra ở chỉ số phủ đáp án (Fixed 20% so với Sentence/Recursive 40%).
>
> **Hạn chế thứ hai:** nhóm chưa thống nhất được bộ câu hỏi. Sáu thành viên chạy trên **ba bộ khác nhau** — Khánh, Vinh, Bá Quân và Huy dùng bộ 5 câu ở Mục 3 dưới đây; Hải và Giáp mỗi người dùng một bộ riêng. `docs/SCORING.md` yêu cầu cả nhóm chạy chung một bộ, nên các con số chỉ so được trong từng cụm.
Chiến lược nào tốt nhất cho chủ đề này? Tại sao?
> Dựa trên bằng chứng hiện có, nhóm **chưa thể kết luận** chiến lược nào thắng, vì phép so sánh bị nhiễu bởi bộ nhúng. Điều nói được chắc chắn: với chủ đề quy định học bổng — vốn là văn bản có heading rõ và số liệu nằm sát nhãn của nó — các chiến lược **bám cấu trúc** (`HeadingChunker`, `RecursiveChunker`) an toàn hơn `FixedSizeChunker`, vì chỉ `FixedSizeChunker` mới có nguy cơ cắt rời con số khỏi ngữ cảnh định danh nó. Phân tích lỗi của Khánh và thiết kế gắn-lại-heading của Hải cùng chỉ về một kết luận: **đơn vị chunk nên trùng với đơn vị ngữ nghĩa của tài liệu**, không phải một con số ký tự cố định.
---
3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)
Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)
#	Loại	Câu hỏi (Query)	Câu trả lời chuẩn (Gold Answer)	Tài liệu chứa thông tin
1	tra số liệu	Mức học bổng dành cho sinh viên trúng tuyển ngành Vi mạch bán dẫn tại ĐH Công nghiệp Hà Nội là bao nhiêu tiền một tháng?	4.200.000 đồng/tháng	`haui-financial-aid-scholarships`
2	hỏi điều kiện	Để duy trì học bổng Đinh Thiện Lý, sinh viên cần đạt CGPA tối thiểu bao nhiêu theo thang điểm 10?	CGPA từ 8.0 trở lên (thang điểm 10)	`lstf-dinh-thien-ly-scholarship`
3	hỏi quy trình	Để Quỹ Đinh Thiện Lý giải ngân học bổng, nhà trường cần gửi văn bản gồm những thông tin gì?	(1) Bộ hồ sơ sinh viên, (2) Tổng số tiền học bổng, (3) Thông tin tài khoản ngân hàng	`lstf-dinh-thien-ly-scholarship`
4	liệt kê	Liệt kê các mức phần trăm hỗ trợ trong chính sách miễn, giảm học phí theo Nghị định của Chính phủ?	3 mức: 100%, 70% và 50% học phí	`hust-financial-aid-for-students`
5	bẫy metadata	Tiêu chuẩn về kết quả học tập để sinh viên được nhận hỗ trợ 100% học phí là gì?	Không có tiêu chuẩn về kết quả học tập — chỉ cần thuộc diện chính sách theo quy định	`hust-financial-aid-for-students`
Câu 5 là câu cần lọc metadata. Câu hỏi cố ý không nêu người hỏi là ai. Corpus có `hust-postgrad-research-scholarships` (`audience=faculty`) cũng nói về "học bổng toàn phần bằng 100% học phí" nhưng với điều kiện hoàn toàn khác (CPA từ 3.2, hoặc là tác giả chính của bài báo ISI/Scopus). Không lọc thì hai tài liệu lẫn nhau và agent trả lời sai đối tượng.
Tổng hợp chất lượng truy xuất của nhóm
Số liệu dưới đây lấy từ lần chạy có mô hình thật của Vinh (`BAAI/bge-m3` + `Qwen2.5-1.5B-Instruct`, `RecursiveChunker(350)`), vì đây là lần chạy duy nhất đo được cả hai vế của rubric: truy xuất và câu trả lời của agent.
#	Câu hỏi	Target rank	Có chunk liên quan trong top-3?	Độ tương đồng câu trả lời	Điểm
1	Vi mạch bán dẫn HaUI	Top-1	Có	0.9390 — sinh đúng "4.200.000 đồng/tháng"	2
2	CGPA Đinh Thiện Lý	Top-1	Có	0.5103 — trả lời cụt "8.0", thiếu ngữ cảnh thang điểm	1
3	Quy trình giải ngân	Top-1	Có	0.7172 — liệt kê thiếu, không đủ 3 mục	1
4	Các mức miễn giảm học phí	Top-1	Có	0.8372 — đúng đủ 100%/70%/50%	2
5	Bẫy metadata	Top-3	Có	0.4862 — trả lời "Không có thông tin"	1
			5/5	Trung bình 0.6980	7/10
Tách bạch hai vế: truy xuất đạt top-3 hit 5/5 (100%) và top-1 hit 4/5 (80%), nhưng chỉ 2/5 câu có câu trả lời vượt ngưỡng tương đồng 0.80 so với gold.
Cách đọc trực giác là đổ lỗi cho LLM: retrieval đã lấy đúng tài liệu rồi, vậy lỗi phải nằm ở khâu sinh câu trả lời. Nhóm đã kiểm chứng giả thuyết này và nó SAI.
Huy chạy một thí nghiệm cô lập biến số: giữ nguyên hoàn toàn tầng truy xuất (`RecursiveChunker(350)` + MiniLM, 203 chunk, cùng ngữ cảnh top-3), chỉ đổi mô hình sinh câu trả lời giữa Gemini 3.6 Flash và DeepSeek Chat — hai mô hình khác hãng, khác kiến trúc, khác hẳn quy mô.
Câu	Q1	Q2	Q3	Q4	Q5	Tổng
Gemini 3.6 Flash	1	1	1	2	0	5/10
DeepSeek Chat	1	1	1	2	0	5/10
Điểm không xê dịch một chút nào. Hai mô hình cùng thắng ở Q4, cùng thua ở Q1, Q3, Q5, và cùng trả lời đúng câu "Không có thông tin." ở những chỗ ngữ cảnh không chứa đáp án. Nếu LLM là nút thắt thì thay hẳn LLM phải làm điểm thay đổi; nó không thay đổi.
Nút thắt thật nằm ở chunking, không phải ở LLM. Lý do con số 5/5 gây hiểu nhầm: "top-3 hit" đo ở mức tài liệu, mà tài liệu đúng nằm trong top-3 không có nghĩa là đoạn văn chứa đáp án nằm trong đó. Đây đúng là lỗi "đúng tài liệu, sai mảnh" mà Giáp mô tả trong báo cáo cá nhân, và cũng là thứ chỉ số phủ đáp án của Huy đo được còn Hit@3 thì không.
Ba nguồn độc lập cùng chỉ về một kết luận: Giáp (OpenAI, chiến lược heading) qua phân tích lỗi thủ công, Huy qua chỉ số phủ đáp án ở mức chunk, và Huy qua đối chứng đổi LLM. Không phải suy đoán từ một lần chạy.
Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?
> Có, và đo được ở **Câu 5**. Kết quả A/B thực nghiệm:
```
Khong loc:
  1. haui-financial-aid-scholarships#5       +0.6802  aud=student
  2. hust-postgrad-research-scholarships#1   +0.6716  aud=faculty   <-- chen vao
  3. haui-financial-aid-scholarships#21      +0.6681  aud=student
  => tai lieu dung (hust-financial-aid) BI DAY RA NGOAI top-3

Co loc {audience: student}:
  1. haui-financial-aid-scholarships#5       +0.6802  aud=student
  2. haui-financial-aid-scholarships#21      +0.6681  aud=student
  3. hust-financial-aid-for-students#2       +0.6578  aud=student   <-- MATCH
```
> Tài liệu `faculty` xếp hạng 2 khi không lọc, đẩy tài liệu `student` đúng ra khỏi top-3. Bật filter thì tài liệu đúng quay lại. Đây là bằng chứng trực tiếp rằng metadata filter có việc thật để làm chứ không phải trang trí.
---
4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)
Những phân tích hay nhất nhóm sẽ trình bày:
> 1. **Bộ nhúng quan trọng hơn chiến lược chunking.** Cùng corpus, cùng bộ câu hỏi: `MockEmbedder` cho 0–2/5, `BAAI/bge-m3` cho 5/5. Khoảng cách do đổi bộ nhúng lớn hơn mọi khác biệt giữa ba chiến lược chunking cộng lại.
> 2. **Truy xuất đúng không có nghĩa là trả lời đúng — và thủ phạm là chunking, không phải LLM.** Top-3 hit 5/5 nhưng chỉ 2/5 câu trả lời đạt ngưỡng. Nhóm đã kiểm chứng bằng cách đổi hẳn LLM (Gemini 3.6 Flash so với DeepSeek Chat) trên cùng một tầng truy xuất: điểm **giữ nguyên 5/10 ở cả hai**. Nếu chỉ báo cáo Hit@3 thì hệ thống trông như hoàn hảo, trong khi 3/5 câu người dùng vẫn nhận câu trả lời sai hoặc cụt.
> 3. **Bẫy metadata chỉ "nổ" ở một số cấu hình.** Với `bge-m3` (Vinh), Gemini (Bá Quân) và OpenAI (Giáp), tài liệu `faculty` chen vào top-3 và đẩy tài liệu đúng ra ngoài; filter kéo lại được. Nhưng đối chứng của Huy cho thấy điều kiện hẹp hơn nhiều: với MiniLM thì **không chiến lược nào** kích hoạt được bẫy, còn với Gemini embedding thì **chỉ Recursive** kích hoạt (faculty xếp hạng 2), Fixed và Sentence vẫn không. Vậy bẫy phụ thuộc **cả bộ nhúng lẫn chiến lược chunking** — nói "filter có hiệu quả" mà không nêu cấu hình là chưa đủ.
> 4. **Hai thành viên độc lập cùng phát hiện một lỗ hổng trong cách chấm.** Giáp (OpenAI, chiến lược heading) và Huy (MiniLM, đối chứng 3 chiến lược) không dùng chung bộ câu hỏi, không dùng chung bộ nhúng, nhưng cùng kết luận: **chấm theo `doc_id` che mất toàn bộ khác biệt giữa các chiến lược**. Giáp: 5/5 theo tài liệu nhưng 3/5 theo nội dung. Huy: cả ba chiến lược đều Hit@3 80%, chỉ chỉ số phủ đáp án mới tách được 20% với 40%. Sự hội tụ từ hai hướng độc lập khiến kết luận này đáng tin hơn bất kỳ con số đơn lẻ nào trong báo cáo.
Bài học rút ra khi so sánh trong nhóm:
> Bài học đắt nhất không phải về chunking mà về **thiết kế thí nghiệm**: nhóm đã để hai biến số cùng thay đổi (chiến lược chunking *và* bộ nhúng), nên không tách được ảnh hưởng của từng cái. Ba con số 0/5, 2/5, 5/5 nhìn như một bảng xếp hạng chiến lược nhưng thực chất là bảng xếp hạng bộ nhúng. Muốn so sánh chiến lược cho ra kết luận, cả nhóm phải cố định bộ nhúng trước.
Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu?
> Bốn điều. Không, **thống nhất bộ câu hỏi và bộ nhúng ngay từ đầu** — hiện nhóm có 3 bộ câu hỏi và 5 bộ nhúng khác nhau, nên phần lớn số liệu không so sánh chéo được. Một, **thống nhất bộ nhúng ngay từ đầu** — `bge-m3` chạy offline được trên máy cá nhân nên không có lý do gì để hai thành viên phải dùng `MockEmbedder`. Hai, **thay 2 tài liệu lỗi thời** (2019 và 2022) bằng bản mới, hoặc bổ sung tài liệu `faculty` còn hiệu lực, để bẫy metadata không phải dựa vào dữ liệu hết hạn. Ba, **đo ở mức chunk chứ không chỉ mức tài liệu** — thêm chỉ số kiểm tra xem con số trong gold answer có thực sự nằm trong ngữ cảnh truy xuất hay không, vì Hit@3 đã tỏ ra quá dễ để phân biệt các chiến lược. Bốn, **thử hướng small-to-big** mà Giáp đề xuất: dùng chunk nhỏ (~200 ký tự) để so khớp nhưng trả về cả mục cha cho agent đọc, tức tách "đơn vị để tìm" khỏi "đơn vị để hiểu" — hướng này sửa đúng lỗi "đúng tài liệu, sai mảnh" mà cả Giáp và Huy đều đo được.
---
Tự Đánh Giá (Phần Nhóm)
Tiêu chí	Điểm tự đánh giá	Căn cứ
Lựa chọn tài liệu (Document Set Quality)	8 / 10	Đủ 8 tài liệu, metadata đầy đủ, `sources.csv` khớp 1-1, đã vá 3 lỗi dữ liệu. Trừ điểm vì 2 tài liệu lỗi thời (2019, 2022).
Thiết kế chiến lược (Strategy Design)	11 / 15	Ba chiến lược khác biệt thật, có 1 chiến lược custom theo heading đúng yêu cầu riêng của L3A. Trừ điểm vì thí nghiệm không cố định bộ nhúng nên không kết luận được chiến lược nào tốt hơn.
Chất lượng truy xuất (Retrieval Quality)	7 / 10	Top-3 hit 5/5, top-1 hit 4/5, bẫy metadata chứng minh được bằng A/B. Trừ điểm vì chỉ 2/5 câu trả lời của agent đạt ngưỡng 0.80.
Thuyết trình (Demo)	4 / 5	Có 3 insight đo được kèm số liệu và 1 bài học về thiết kế thí nghiệm.
Tổng phần nhóm	30 / 40	
