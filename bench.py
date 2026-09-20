"""Benchmark retrieval cho corpus học bổng — dùng chung cả nhóm.

Mỗi thành viên CHỈ đổi dòng `STRATEGY` bên dưới; corpus, câu hỏi, embedder, top_k giữ nguyên
để so sánh công bằng.

    python bench.py                    # chạy STRATEGY, ghi ket_qua_benchmark.txt
    python bench.py --all              # chạy cả 6 chiến lược, in bảng tổng hợp

Biến môi trường (đọc từ .env):
    EMBEDDING_PROVIDER = mock | local | openai | gemini   (mặc định mock — KHÔNG có ngữ nghĩa)
    LLM_PROVIDER       = none | openai | gemini           (mặc định none — agent trả lời kiểu trích đoạn)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import (
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

# ─── Mỗi người chỉ đổi dòng này ─────────────────────────────────────────────────
STRATEGY = "heading"  # fixed | sentence | recursive | heading | heading_ctx | small_to_big
# ─────────────────────────────────────────────────────────────────────────────────

DATA_DIR = Path("data/scholarship_final/scholarship")
OUTPUT_FILE = Path("ket_qua_benchmark.txt")
CHUNK_SIZE = 500
TOP_K = 3
MIN_SECTION = 150  # heading_ctx: mục ngắn hơn ngưỡng này được gộp vào mục kế tiếp
CHILD_SIZE = 200  # small_to_big: kích thước chunk con dùng để truy xuất

# 5 câu hỏi benchmark — BẢN NHÁP, R2 thay bằng bộ câu nhóm chốt.
# gold: doc_id chứa đáp án; answer_key: regex phải xuất hiện trong ngữ cảnh truy xuất được;
# filter: metadata_filter dùng khi chạy (câu có filter sẽ được chạy thêm bản không filter để A/B).
QUERIES = [
    {   # tra số liệu
        "question": "Học bổng khuyến khích học tập loại A ở Bách khoa Hà Nội yêu cầu GPA và điểm rèn luyện bao nhiêu?",
        "gold": ["hust-financial-aid-for-students"],
        "answer_key": r"GPA từ 3\.6, điểm rèn luyện từ 90",
        "gold_answer": "Loại A (150% học phí): GPA từ 3.6 và điểm rèn luyện từ 90.",
        "filter": None,
    },
    {   # cần filter: câu hỏi không nói người hỏi là ai; tài liệu "faculty" (UED, học bổng thạc sĩ/
        # tiến sĩ VINIF) có mục "## Trách nhiệm của người nhận học bổng" khớp gần nguyên văn và chiếm
        # top-1/2 khi không lọc (báo cáo 6 tháng/lần — sai đối tượng với sinh viên đại học).
        "question": "Người nhận học bổng có trách nhiệm gì?",
        "gold": ["lstf-dinh-thien-ly-scholarship"],
        "answer_key": r"ít nhất 4 dự án|từ \*\*2 trở lên",
        "gold_answer": "Với sinh viên (học bổng Đinh Thiện Lý): duy trì CGPA từ 2 trở lên (thang 4) hoặc 8.0 (thang 10), "
                       "không trượt môn; báo Quỹ mọi thay đổi kế hoạch học tập; tham gia ít nhất 4 dự án/sự kiện "
                       "mỗi năm và bắt buộc dự Lễ trao học bổng.",
        "filter": {"audience": "student"},
    },
    {   # quy trình / thời hạn
        "question": "Sinh viên USTH phải nộp hồ sơ học bổng Vallet về Phòng Công tác sinh viên trước ngày nào?",
        "gold": ["usth-vallet-scholarship-2026"],
        "answer_key": r"24/06/2026",
        "gold_answer": "Trước ngày 24/06/2026 (đơn đăng ký gửi về Khoa trước 15h00 ngày 21/05/2026).",
        "filter": None,
    },
    {   # liệt kê
        "question": "Học bổng khuyến khích học tập của Đại học Công nghiệp Hà Nội có những mức nào?",
        "gold": ["haui-financial-aid-scholarships"],
        "answer_key": r"Học bổng Giỏi \(Bán phần\)",
        "gold_answer": "Xuất sắc (toàn phần, 3.60–4.0 + rèn luyện 90–100), Giỏi (bán phần, 3.20–3.59 + ≥80), "
                       "Khá (bán phần, 2.50–3.19 + ≥70).",
        "filter": None,
    },
    {   # tra số liệu
        "question": "Học bổng Sigma Gold trị giá bao nhiêu mỗi tháng?",
        "gold": ["viasm-sigma-gold-scholarship"],
        "answer_key": r"15 triệu đồng/tháng",
        "gold_answer": "15 triệu đồng/tháng, cấp 10 tháng mỗi năm học, tối đa 10 suất.",
        "filter": None,
    },
]


# ─── Đọc corpus ──────────────────────────────────────────────────────────────────
def load_corpus(data_dir: Path) -> list[tuple[dict, str]]:
    """Trả về [(frontmatter, body)] cho mọi file .md; frontmatter là các dòng `key: value`."""
    corpus = []
    for path in sorted(data_dir.glob("*.md")):
        _, front, body = path.read_text(encoding="utf-8").split("---", 2)
        meta = {}
        for line in front.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"').strip("'")
        corpus.append((meta, body.strip()))
    return corpus


# ─── Chunkers ────────────────────────────────────────────────────────────────────
def split_sections(text: str) -> list[dict]:
    """Tách trước mỗi dòng `##`/`###`; ghi lại tiêu đề mục và tiêu đề `##` cha."""
    sections, parent = [], ""
    for block in re.split(r"(?m)^(?=#{2,3} )", text):
        block = block.strip()
        if not block:
            continue
        first = block.splitlines()[0]
        title = first if first.startswith("#") else ""
        if title.startswith("## "):
            parent = title[3:].strip()
        sections.append({"title": title, "parent": parent, "text": block})
    return sections


def split_long(section_text: str, title: str, size: int) -> list[str]:
    """Mục dài quá `size` thì cắt recursive và gắn lại tiêu đề vào từng mảnh con."""
    if len(section_text) <= size:
        return [section_text]
    body = section_text[len(title):] if title else section_text
    pieces = RecursiveChunker(chunk_size=max(100, size - len(title) - 1)).chunk(body)
    return [f"{title}\n{piece}" if title else piece for piece in pieces]


def chunk_heading(text: str, meta: dict) -> list[str]:
    return [c for s in split_sections(text) for c in split_long(s["text"], s["title"], CHUNK_SIZE)]


def chunk_heading_ctx(text: str, meta: dict) -> list[str]:
    # Gộp mục quá ngắn (thường chỉ là tiêu đề/menu) vào mục kế tiếp.
    merged, carry = [], ""
    for s in split_sections(text):
        s = dict(s, text=f"{carry}\n\n{s['text']}".strip() if carry else s["text"])
        if len(s["text"]) < MIN_SECTION:
            carry = s["text"]
            continue
        carry = ""
        merged.append(s)
    if carry:
        if merged:
            merged[-1]["text"] += "\n\n" + carry
        else:
            merged.append({"title": "", "parent": "", "text": carry})

    chunks = []
    for s in merged:
        header = f"[{meta.get('title', '')}]" + (f" › {s['parent']}" if s["parent"] else "")
        for piece in split_long(s["text"], s["title"], CHUNK_SIZE - len(header) - 1):
            chunks.append(f"{header}\n{piece}")
    return chunks


STRATEGIES = {
    "fixed": lambda text, meta: FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=50).chunk(text),
    "sentence": lambda text, meta: SentenceChunker(max_sentences_per_chunk=3).chunk(text),
    "recursive": lambda text, meta: RecursiveChunker(chunk_size=CHUNK_SIZE).chunk(text),
    "heading": chunk_heading,
    "heading_ctx": chunk_heading_ctx,
    "small_to_big": None,  # xử lý riêng trong build_documents
}


def build_documents(corpus: list[tuple[dict, str]], strategy: str) -> tuple[list[Document], dict[str, str]]:
    """Chunk ngoài store; mỗi chunk là một Document mang đủ frontmatter + doc_id của file gốc."""
    docs, parents = [], {}
    for meta, body in corpus:
        doc_id = meta["doc_id"]
        if strategy == "small_to_big":
            # Con nhỏ để truy xuất chính xác; cha là cả mục để agent đủ ngữ cảnh.
            for p_index, section in enumerate(split_sections(body)):
                parent_id = f"{doc_id}@{p_index}"
                parents[parent_id] = section["text"]
                for child in RecursiveChunker(chunk_size=CHILD_SIZE).chunk(section["text"]):
                    docs.append(Document(
                        id=f"{doc_id}#{len(docs)}",
                        content=child,
                        metadata={**meta, "doc_id": doc_id, "parent_id": parent_id},
                    ))
        else:
            for i, chunk in enumerate(STRATEGIES[strategy](body, meta)):
                docs.append(Document(id=f"{doc_id}#{i}", content=chunk, metadata={**meta, "doc_id": doc_id, "chunk_index": i}))
    return docs, parents


class RetrievalView:
    """Góc nhìn của agent lên store: áp metadata_filter và (small_to_big) thay chunk con bằng mục cha.

    KnowledgeBaseAgent chỉ gọi `.search(query, top_k)`, nên truyền view này vào thay cho store.
    """

    def __init__(self, store: EmbeddingStore, metadata_filter: dict | None, parents: dict[str, str]) -> None:
        self.store, self.metadata_filter, self.parents = store, metadata_filter, parents

    def search(self, query: str, top_k: int = TOP_K) -> list[dict]:
        if not self.parents:
            return self.store.search_with_filter(query, top_k=top_k, metadata_filter=self.metadata_filter)
        results, seen = [], set()
        for hit in self.store.search_with_filter(query, top_k=top_k * 5, metadata_filter=self.metadata_filter):
            parent_id = hit["metadata"]["parent_id"]
            if parent_id in seen:
                continue
            seen.add(parent_id)
            results.append({**hit, "content": self.parents[parent_id]})
            if len(results) == top_k:
                break
        return results


# ─── Embedder + LLM ─────────────────────────────────────────────────────────────
class CachedEmbedder:
    """Cache embedding theo hash nội dung để chạy lại không gọi API lần nữa."""

    def __init__(self, embedder, name: str) -> None:
        self.embedder, self._backend_name = embedder, name
        self.path = Path(".cache") / f"embeddings-{re.sub(r'[^A-Za-z0-9_.-]', '_', name)}.json"
        self.cache = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def __call__(self, text: str) -> list[float]:
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if key not in self.cache:
            self.cache[key] = self.embedder(text)
        return self.cache[key]

    def save(self) -> None:
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(json.dumps(self.cache), encoding="utf-8")


def make_embedder():
    provider = os.getenv("EMBEDDING_PROVIDER", "mock").strip().lower()
    try:
        if provider == "local":
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        if provider == "openai":
            model = os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
            return CachedEmbedder(OpenAIEmbedder(model_name=model), model)
        if provider == "gemini":
            model = os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL)
            return CachedEmbedder(GeminiEmbedder(model_name=model), model)
    except Exception as error:  # thiếu thư viện / API key -> quay về mock, nhưng báo rõ
        print(f"[!] Không khởi tạo được embedder '{provider}' ({error}); dùng mock.", file=sys.stderr)
    return _mock_embed


def extractive_stub(prompt: str) -> str:
    # Không có LLM: trả nguyên đoạn ngữ cảnh [1] để vẫn thấy agent "đọc" được gì.
    match = re.search(r"\[1\] \(nguồn: [^)]*\)\n(.*?)(?:\n\n\[2\]|\n\nCÂU HỎI:)", prompt, re.S)
    return "(stub) " + (match.group(1) if match else prompt)[:300].replace("\n", " ")


def make_llm():
    provider = os.getenv("LLM_PROVIDER", "none").strip().lower()
    try:
        if provider == "openai":
            from openai import OpenAI

            client, model = OpenAI(), os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
            name, call = f"openai:{model}", lambda prompt: client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}], temperature=0
            ).choices[0].message.content
        elif provider == "gemini":
            from google import genai

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
            model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
            name, call = f"gemini:{model}", lambda prompt: client.models.generate_content(model=model, contents=prompt).text
        else:
            return "stub (không có LLM)", extractive_stub
    except Exception as error:
        print(f"[!] Không khởi tạo được LLM '{provider}' ({error}); dùng stub trích đoạn.", file=sys.stderr)
        return "stub (không có LLM)", extractive_stub

    def safe_call(prompt: str) -> str:
        try:
            return call(prompt)
        except Exception as error:  # sai tên model / hết quota: không làm sập cả lượt benchmark
            print(f"[!] Gọi LLM lỗi ({type(error).__name__}: {error}); dùng stub cho câu này.", file=sys.stderr)
            return extractive_stub(prompt)

    return name, safe_call


# ─── Chạy benchmark ─────────────────────────────────────────────────────────────
def grade(results: list[dict], query: dict) -> dict:
    """Chấm hai mức: đúng tài liệu (doc-level) và ngữ cảnh chứa đáp án (content-level)."""
    ranks = [i for i, r in enumerate(results, start=1) if r["metadata"]["doc_id"] in query["gold"]]
    gold_rank = ranks[0] if ranks else None
    answer_found = any(re.search(query["answer_key"], r["content"]) for r in results)
    if not answer_found or gold_rank is None:
        points = 0
    elif gold_rank == 1:
        points = 2
    else:
        points = 1
    return {"gold_rank": gold_rank, "doc_hit": gold_rank is not None, "answer_found": answer_found, "points": points}


def run(strategy: str, corpus, embedder, llm_name: str, llm_fn, out) -> dict:
    docs, parents = build_documents(corpus, strategy)
    store = EmbeddingStore(collection_name=f"bench_{strategy}", embedding_fn=embedder)
    store.add_documents(docs)
    lengths = [len(d.content) for d in docs]

    out(f"# Benchmark — strategy={strategy}")
    out(f"Embedder: {getattr(embedder, '_backend_name', type(embedder).__name__)} | LLM: {llm_name} | top_k={TOP_K}")
    out(f"Đã nạp {store.get_collection_size()} chunk từ {len(corpus)} tài liệu "
        f"(avg {sum(lengths) // len(lengths)} ký tự, max {max(lengths)}, <100 ký tự: {sum(n < 100 for n in lengths)})")
    if getattr(embedder, "_backend_name", "") == "mock embeddings fallback":
        out("[!] MockEmbedder không mã hoá ngữ nghĩa — thứ hạng dưới đây gần như ngẫu nhiên, chỉ dùng để kiểm luồng.")

    summary = []
    for number, query in enumerate(QUERIES, start=1):
        runs = [("có filter", query["filter"]), ("KHÔNG filter", None)] if query["filter"] else [("", None)]
        for label, metadata_filter in runs:
            view = RetrievalView(store, metadata_filter, parents)
            results = view.search(query["question"], top_k=TOP_K)
            graded = grade(results, query)
            answer = KnowledgeBaseAgent(store=view, llm_fn=llm_fn).answer(query["question"], top_k=TOP_K)

            out(f"\n## Q{number}{f' ({label})' if label else ''}: {query['question']}")
            if metadata_filter:
                out(f"filter: {metadata_filter}")
            out(f"gold: {', '.join(query['gold'])} | đáp án chuẩn: {query['gold_answer']}")
            for rank, r in enumerate(results, start=1):
                preview = re.sub(r"\s+", " ", r["content"])[:140]
                mark = "✓" if r["metadata"]["doc_id"] in query["gold"] else " "
                out(f"  {rank}. {mark} score={r['score']:.3f} [{r['metadata']['audience']}] {r['id']} :: {preview}")
            out(f"  → gold ở top-{graded['gold_rank'] or '-'} | ngữ cảnh chứa đáp án: "
                f"{'có' if graded['answer_found'] else 'KHÔNG'} | điểm: {graded['points']}/2")
            answer_preview = re.sub(r"\s+", " ", answer)[:300]
            out(f"  agent: {answer_preview}")
            if label != "KHÔNG filter":
                summary.append(graded)

    doc_hits = sum(g["doc_hit"] for g in summary)
    answer_hits = sum(g["doc_hit"] and g["answer_found"] for g in summary)
    points = sum(g["points"] for g in summary)
    out(f"\n# Tổng: đúng tài liệu trong top-{TOP_K}: {doc_hits}/{len(summary)} | "
        f"ngữ cảnh thật sự chứa đáp án: {answer_hits}/{len(summary)} | điểm: {points}/{2 * len(summary)}")
    return {"strategy": strategy, "chunks": len(docs), "avg": sum(lengths) // len(lengths),
            "doc_hits": doc_hits, "answer_hits": answer_hits, "points": points}


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark retrieval cho corpus học bổng")
    parser.add_argument("--strategy", choices=STRATEGIES, default=STRATEGY)
    parser.add_argument("--all", action="store_true", help="chạy cả 6 chiến lược và in bảng tổng hợp")
    args = parser.parse_args()

    load_dotenv(override=False)
    corpus = load_corpus(DATA_DIR)
    bodies = {meta["doc_id"]: body for meta, body in corpus}
    for number, query in enumerate(QUERIES, start=1):  # gold answer phải trích được từ tài liệu thật
        if not any(re.search(query["answer_key"], bodies.get(doc_id, "")) for doc_id in query["gold"]):
            print(f"[!] Q{number}: answer_key không có trong tài liệu gold — sửa lại câu hỏi.", file=sys.stderr)
    embedder = make_embedder()
    llm_name, llm_fn = make_llm()

    if args.all:
        rows = [run(name, corpus, embedder, llm_name, llm_fn, out=lambda line: None) for name in STRATEGIES]
        print(f"{'strategy':14}{'chunks':>7}{'avg':>6}  đúng-tài-liệu  chứa-đáp-án  điểm")
        for r in rows:
            print(f"{r['strategy']:14}{r['chunks']:>7}{r['avg']:>6}  {r['doc_hits']:>9}/{len(QUERIES)}"
                  f"  {r['answer_hits']:>9}/{len(QUERIES)}  {r['points']:>3}/{2 * len(QUERIES)}")
    else:
        lines: list[str] = []

        def out(line: str) -> None:
            print(line)
            lines.append(line)

        run(args.strategy, corpus, embedder, llm_name, llm_fn, out)
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nĐã ghi {OUTPUT_FILE}")

    if isinstance(embedder, CachedEmbedder):
        embedder.save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
