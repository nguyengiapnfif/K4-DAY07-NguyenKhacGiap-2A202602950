# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "beautifulsoup4", "markdownify"]
# ///
"""Crawl trang học bổng/hỗ trợ tài chính công khai của VinUni thành corpus Markdown sạch.

Khác crawler mẫu `fetch_public_pages.py` ở ba điểm:
- đọc robots.txt bằng chính User-Agent của lab (VinUni trả 403 cho `Python-urllib`,
  khiến RobotFileParser.read() hiểu nhầm là cấm toàn bộ);
- chỉ giữ vùng nội dung chính (bỏ menu, sidebar, mục lục, bài liên quan) và giữ bảng/danh sách;
- với trang policy.vinuni.edu.vn: đọc tab "Status and Details" để lấy số hiệu + ngày ban hành
  làm `document_version`, và bỏ qua văn bản không có Security Classification = Public.
Cột tuỳ chọn `sections` (regex trên tiêu đề `###`) tách một trang gộp nhiều audience thành nhiều file.

Chạy từ thư mục gốc repo:
    uv run scripts/crawl_vinuni.py data/urls.csv --output-dir data/hoc-bong
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

USER_AGENT = "Day7DataFoundationsCourse/1.0 (+educational-lab)"
REQUIRED_COLUMNS = ["url", "doc_id", "title", "audience"]
# Thử lần lượt: nội dung policy, bài tin tức admissions, trang tĩnh admissions, fallback.
CONTENT_SELECTORS = ["#single_current_version", "article.contentEditorPost", "main .pageArticle", "article", "main"]
NOISE_SELECTORS = [
    "script", "style", "noscript", "svg", "img", "iframe", "form", "nav", "aside",
    ".sidebarWrapper", ".menu_single_sidebar", ".breadcrumb", ".breadcrumbs", ".relatedPosts__bg",
    ".social-share", ".default-banner",
]
MANIFEST_FIELDS = ["doc_id", "file_path", "title", "source_url", "retrieved_at", "document_version", "license_or_permission"]


def robots_allowed(url: str, session: requests.Session, cache: dict[str, RobotFileParser]) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    if robots_url not in cache:
        parser = RobotFileParser(robots_url)
        response = session.get(robots_url, timeout=20)
        if response.status_code in (401, 403):
            parser.disallow_all = True
        elif response.status_code >= 400:
            parser.allow_all = True
        else:
            parser.parse(response.text.splitlines())
        cache[robots_url] = parser
    return cache[robots_url].can_fetch(USER_AGENT, url)


def policy_status(soup: BeautifulSoup) -> dict[str, str]:
    """Đọc các cặp 'Nhãn:' / giá trị trong tab Status and Details của policy.vinuni.edu.vn."""
    tab = soup.select_one("#status_details")
    if not tab:
        return {}
    lines = tab.get_text("\n", strip=True).splitlines()
    return {lines[i].rstrip(":"): lines[i + 1] for i in range(len(lines) - 1) if lines[i].endswith(":")}


def extract_markdown(soup: BeautifulSoup, fallback_title: str) -> str:
    node = next((found for sel in CONTENT_SELECTORS if (found := soup.select_one(sel))), None)
    if node is None:
        raise ValueError("không tìm thấy vùng nội dung chính")
    for noise in node.select(",".join(NOISE_SELECTORS)):
        noise.decompose()
    # Tiêu đề accordion nằm trong <button>; HTML dán từ Word thì bold/italic vụn trong bảng và heading.
    for tag in node.select("button, td strong, td b, td em, td i, th strong, th b, th em, th i, "
                           "h1 strong, h2 strong, h3 strong, h4 strong, h2 b, h3 b, h4 b"):
        tag.unwrap()
    md = markdownify(str(node), heading_style="ATX", bullets="-", strip=["a", "span"])
    md = md.replace("\xa0", " ")
    md = re.sub(r"\*\*(\s*)\*\*", r"\1", md)  # gộp các đoạn bold liền kề
    md = re.sub(r"\*\*([,.;:])\*\*", r"\1", md)  # dấu câu bị bôi đậm riêng
    md = re.sub(r"^#+\s*$", "", md, flags=re.M)  # heading rỗng
    md = re.sub(r"^.*\[email(?:&#160;|\s)protected\].*$", "", md, flags=re.M)  # email bị Cloudflare che
    md = re.sub(r"(?<=\S) {2,}", " ", md)
    md = "\n".join(line.rstrip() for line in md.splitlines())
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    if not md.startswith("# "):
        md = f"# {fallback_title}\n\n{md}"
    return md


def filter_sections(md: str, pattern: str) -> str:
    """Giữ phần mở đầu và các mục `###` có tiêu đề khớp regex; tiền tố `!` = loại các mục khớp.

    Dùng khi một trang gộp nội dung cho nhiều audience: khai báo cùng URL ở nhiều dòng CSV,
    mỗi dòng một `doc_id`/`audience` và một `sections` khác nhau.
    """
    exclude = pattern.startswith("!")
    regex = re.compile(pattern.lstrip("!"), re.I)
    blocks = re.split(r"(?m)^(?=### )", md)
    kept = [blocks[0]] + [b for b in blocks[1:] if bool(regex.search(b.splitlines()[0])) != exclude]
    if len(kept) == 1:
        raise ValueError(f"không có mục nào khớp sections={pattern!r}")
    return "".join(kept).strip()


def yaml_value(value: str) -> str:
    return f'"{value}"' if re.search(r"(: | #|^[\"'&*!|>%@`])", value) else value


def build_document(row: dict[str, str], url: str, soup: BeautifulSoup, retrieved_at: str) -> tuple[dict[str, str], str]:
    status = policy_status(soup)
    if status and status.get("Security Classification", "").lower() != "public":
        raise ValueError(f"Security Classification = {status.get('Security Classification')!r}, không phải Public")

    version = row.get("document_version") or "not-stated"
    if version == "auto":
        ref, issued = status.get("Reference Number"), status.get("Issuing Date")
        if ref and issued:
            version = f"{ref} ({datetime.strptime(issued, '%b %d, %Y').date().isoformat()})"
        else:
            version = ref or "not-stated"

    metadata = {
        "doc_id": row["doc_id"],
        "title": row["title"],
        "source_url": url,
        "retrieved_at": retrieved_at,
        "document_version": version,
        "audience": row["audience"],
        "department": row.get("department") or "not-stated",
        "category": row.get("category") or "not-stated",
        "language": row.get("language") or "en",
    }
    modified = soup.select_one('meta[property="article:modified_time"]')
    if modified and modified.get("content"):
        metadata["page_modified"] = modified["content"][:10]

    body = extract_markdown(soup, row["title"])
    if row.get("sections"):
        body = filter_sections(body, row["sections"])
    front = "\n".join(f"{key}: {yaml_value(value)}" for key, value in metadata.items())
    return metadata, f"---\n{front}\n---\n\n{body}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data/hoc-bong"))
    parser.add_argument("--delay", type=float, default=1.5, help="giây chờ giữa các request (>= 1)")
    args = parser.parse_args()
    if args.delay < 1:
        parser.error("--delay phải >= 1 giây")

    rows = list(csv.DictReader(args.input_csv.open(encoding="utf-8-sig")))
    missing = [col for col in REQUIRED_COLUMNS if rows and col not in rows[0]]
    if not rows or missing:
        parser.error(f"CSV rỗng hoặc thiếu cột: {missing}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html"})
    robots_cache: dict[str, RobotFileParser] = {}
    retrieved_at = date.today().isoformat()
    manifest, failed = [], 0

    for index, row in enumerate(rows):
        url = row["url"].strip()
        if index:
            time.sleep(args.delay)
        try:
            if not robots_allowed(url, session, robots_cache):
                raise PermissionError("robots.txt không cho phép")
            response = session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            metadata, document = build_document(row, response.url, soup, retrieved_at)
        except (requests.RequestException, PermissionError, ValueError) as error:
            failed += 1
            print(f"BỎ QUA {url}: {error}", file=sys.stderr)
            continue

        path = args.output_dir / f"{metadata['doc_id']}.md"
        path.write_text(document, encoding="utf-8")
        manifest.append({
            "doc_id": metadata["doc_id"],
            "file_path": path.as_posix(),
            "title": metadata["title"],
            "source_url": metadata["source_url"],
            "retrieved_at": metadata["retrieved_at"],
            "document_version": metadata["document_version"],
            "license_or_permission": row.get("license_or_permission") or "public-source",
        })
        print(f"OK  {path}  ({len(document):,} ký tự, version={metadata['document_version']})")

    # Giữ lại dòng của tài liệu làm tay (không có trong input CSV) nếu file của nó vẫn còn.
    manifest_path = args.output_dir / "sources.csv"
    crawled_ids = {row["doc_id"] for row in rows}
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8") as handle:
            manifest += [old for old in csv.DictReader(handle)
                         if old["doc_id"] not in crawled_ids and Path(old["file_path"]).exists()]
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(manifest)
    print(f"Xong: {len(manifest)} dòng trong manifest, {failed} bỏ qua -> {manifest_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
