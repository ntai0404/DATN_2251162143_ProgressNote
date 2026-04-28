"""
tvpl_harvester/extractor.py
============================
Logic bôi đen & lọc nội dung từ một trang TVPL.
- extract_page(): DOM extraction + smart line join + metadata.
- Tách biệt hoàn toàn khỏi logic queue/spider.
"""

import re
import logging
from playwright.sync_api import Page

from .config import MIN_CONTENT_LENGTH

log = logging.getLogger("TVPL.Extractor")

# JS dùng trong browser để cào DOM
_EXTRACT_JS = """
() => {
    const container = document.querySelector('#divContentDoc') ||
                      document.querySelector('.content1');
    if (!container) return null;

    const title = document.querySelector('h1')?.innerText.trim() || "";

    // --- Legal Metadata ---
    const meta = { status: '', issued_date: '', effective_date: '' };
    
    // Check specific badges first (High precision)
    const statusBadge = document.querySelector('.vbStatus, .badge-status, .tinhtrang-vb');
    if (statusBadge) {
        const txt = statusBadge.innerText;
        if (txt.includes('Còn hiệu lực')) meta.status = 'Còn hiệu lực';
        else if (txt.includes('Hết hiệu lực')) meta.status = 'Hết hiệu lực';
        else if (txt.includes('Chưa có hiệu lực')) meta.status = 'Chưa có hiệu lực';
    }

    // Scan property tables/lists
    document.querySelectorAll('tr, li').forEach(row => {
        const t = row.innerText || '';
        if (t.includes(':')) {
            const [label, val] = t.split(':').map(s => s.trim());
            if (label.includes('Tình trạng') && !meta.status) {
                if (val.includes('Còn hiệu lực')) meta.status = 'Còn hiệu lực';
                else if (val.includes('Hết hiệu lực')) meta.status = 'Hết hiệu lực';
            }
            if (label.includes('Ngày ban hành') || label.includes('Ban hành')) {
                const m = val.match(/\d{2}\/\d{2}\/\d{4}/);
                if (m) meta.issued_date = m[0];
            }
            if (label.includes('Ngày hiệu lực') || label.includes('Hiệu lực từ')) {
                const m = val.match(/\d{2}\/\d{2}\/\d{4}/);
                if (m) meta.effective_date = m[0];
            }
        }
    });

    // Fallback for status if still empty
    if (!meta.status && document.body.innerText.includes('Còn hiệu lực')) meta.status = 'Còn hiệu lực';
    if (!meta.status && document.body.innerText.includes('Hết hiệu lực')) meta.status = 'Hết hiệu lực';

    // --- Relationship detection ---
    const replaced_by = [], replaces = [];
    document.querySelectorAll('a[href*="/van-ban/"]').forEach(a => {
        const ctx = a.closest('li, tr, p')?.innerText || '';
        if (ctx.match(/thay thế|bị bãi bỏ|bị thay/i))  replaced_by.push(a.innerText.trim());
        else if (ctx.match(/thay thế cho|bãi bỏ văn bản/i)) replaces.push(a.innerText.trim());
    });

    // --- Discover outbound links ---
    const links = Array.from(document.querySelectorAll('a[href*="/van-ban/"]'))
        .map(a => a.href)
        .filter(h => h.startsWith('https://thuvienphapluat.vn/van-ban/'));

    // Clean noise from content
    container.querySelectorAll('.noprint, script, style, .ads').forEach(n => n.remove());

    return { title, raw_text: container.innerText, links, meta, replaced_by, replaces };
}
"""


def _smart_join(text: str) -> str:
    """
    Nối các dòng bị cắt ngang câu do layout HTML.
    Giữ nguyên dấu xuống dòng tại tiêu đề pháp lý (Điều, Chương...).
    """
    lines = text.split("\n")
    result, buf = [], ""

    header_re = re.compile(
        r"^(Điều|Chương|Phần|Mục|Phụ lục|Khoản|Điểm)\s+\d+|^\d+\.",
        re.IGNORECASE,
    )

    for line in lines:
        line = line.strip()
        if not line:
            if buf:
                result.append(buf)
                buf = ""
            continue

        if header_re.match(line):
            if buf:
                result.append(buf)
                buf = ""
            result.append(line)
            continue

        if not buf:
            buf = line
        else:
            last = buf[-1]
            if last in ",;-" or last.islower():
                buf += " " + line
            elif last in ".!?:" or last.isdigit():
                result.append(buf)
                buf = line
            else:
                buf += " " + line

    if buf:
        result.append(buf)
    return "\n\n".join(result)


def extract_page(page: Page, url: str) -> dict | None:
    """
    Cào nội dung + metadata từ một trang văn bản TVPL.

    Returns:
        dict với keys: title, content, meta, replaced_by, replaces, links
        None nếu trang không hợp lệ (không tìm thấy nội dung, quá ngắn, không có tiêu đề).
    """
    import time
    page.goto(url, wait_until="networkidle", timeout=60_000)
    time.sleep(3)

    raw = page.evaluate(_EXTRACT_JS)
    if not raw:
        log.warning(f"[SKIP] No container found: {url}")
        return None

    if not raw["title"]:
        log.warning(f"[SKIP] No title: {url}")
        return None

    content = _smart_join(raw["raw_text"])
    if len(content) < MIN_CONTENT_LENGTH:
        log.warning(f"[SKIP] Content too short ({len(content)} chars): {url}")
        return None

    return {
        "title":       raw["title"],
        "content":     content,
        "meta":        raw["meta"],
        "replaced_by": raw["replaced_by"],
        "replaces":    raw["replaces"],
        "links":       raw["links"],
    }


def build_markdown(result: dict, source_url: str) -> str:
    """
    Tạo file Markdown với YAML frontmatter từ kết quả extract_page().
    Format này tương thích với ContentProcessor của collector_agent.
    """
    meta = result.get("meta", {})
    status = meta.get("status", "") or "Không rõ"
    replaced_by_str = "; ".join(result.get("replaced_by", []))
    replaces_str = "; ".join(result.get("replaces", []))

    frontmatter = (
        "---\n"
        f'title: "{result["title"]}"\n'
        f'status: "{status}"\n'
        f'issued_date: "{meta.get("issued_date", "")}"\n'
        f'effective_date: "{meta.get("effective_date", "")}"\n'
        f'replaced_by: "{replaced_by_str}"\n'
        f'replaces: "{replaces_str}"\n'
        f'source: "{source_url}"\n'
        "---\n"
    )
    return frontmatter + f"\n# {result['title']}\n\n" + result["content"]
