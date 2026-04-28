"""
tvpl_harvester/spider.py
=========================
Queue-based spider — mở rộng link từ các trang đã cào.
- Luôn ưu tiên PRIORITY_URLS trước khi đụng đến hàng chờ.
- Lưu trạng thái vào JSON để resume nếu bị ngắt giữa chừng.
- Tích hợp URL normalization (loại bỏ ?tab=... để chống trùng).
"""

import json
import time
import random
import logging
from pathlib import Path
from playwright.sync_api import Page
from playwright_stealth import Stealth

from .config import PRIORITY_URLS, DISCOVERY_KEYWORDS, SPIDER_DELAY_MIN, SPIDER_DELAY_MAX
from .extractor import extract_page, build_markdown

log = logging.getLogger("TVPL.Spider")


def _normalize(url: str) -> str:
    """Xóa query params + fragments — chống trùng lặp ?tab=3."""
    return url.split("?")[0].split("#")[0].strip()


def _is_relevant(url: str) -> bool:
    return any(k in url.lower() for k in DISCOVERY_KEYWORDS)


class TVPLSpider:
    """
    Spider cào văn bản pháp luật từ TVPL với hai giai đoạn:
    1. Priority Phase: cào đúng PRIORITY_URLS (bắt buộc, theo thứ tự).
    2. Discovery Phase: mở rộng theo link phát hiện được (hàng chờ).

    Args:
        output_dir:  thư mục lưu file Markdown kết quả.
        state_file:  file JSON lưu trạng thái (để resume).
        max_discovery: số văn bản tối đa cào ở Discovery Phase (0 = tắt).
    """

    def __init__(self, output_dir: Path, state_file: Path, max_discovery: int = 0):
        self.output_dir = output_dir
        self.state_file = state_file
        self.max_discovery = max_discovery
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    # ------------------------------------------------------------------ state

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"processed": [], "queue": [], "priority_done": False}

    def _save_state(self):
        self.state_file.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _is_processed(self, url: str) -> bool:
        return _normalize(url) in self._state["processed"]

    def _mark_processed(self, url: str):
        n = _normalize(url)
        if n not in self._state["processed"]:
            self._state["processed"].append(n)

    def _enqueue(self, urls: list[str]):
        """Thêm links mới (đã lọc, đã normalize) vào hàng chờ."""
        for url in urls:
            n = _normalize(url)
            if (
                n not in self._state["processed"]
                and n not in self._state["queue"]
                and _is_relevant(n)
            ):
                self._state["queue"].append(n)

    # ----------------------------------------------------------------- core

    def _harvest_one(self, page: Page, url: str) -> bool:
        """Cào 1 URL. Trả về True nếu thành công."""
        norm = _normalize(url)
        if self._is_processed(norm):
            return False

        log.info(f"→ Harvesting: {norm}")
        result = extract_page(page, norm)
        if result is None:
            self._mark_processed(norm)
            return False

        md_text = build_markdown(result, norm)
        safe = "".join(c if c.isalnum() else "_" for c in result["title"][:100])
        out_path = self.output_dir / f"{safe}.md"
        out_path.write_text(md_text, encoding="utf-8")
        log.info(f"  ✅ Saved: {out_path.name}  [{result['meta'].get('status', '?')}]")

        # Đẩy link phát hiện được vào hàng chờ
        self._enqueue(result.get("links", []))
        self._mark_processed(norm)
        self._save_state()
        return True

    def run(self, context):
        """
        Chạy spider qua 2 giai đoạn.
        context: BrowserContext đã login (từ TVPLBrowser).
        """
        page: Page = context.new_page()
        Stealth().apply_stealth_sync(page)

        # ── Phase 1: Priority (7 văn bản bắt buộc) ──────────────────────────
        if not self._state["priority_done"]:
            log.info("=== Phase 1: Priority Harvest ===")
            for url in PRIORITY_URLS:
                if not self._is_processed(url):
                    try:
                        self._harvest_one(page, url)
                    except Exception as e:
                        log.error(f"Failed to harvest priority {url}: {e}")
                    time.sleep(random.uniform(SPIDER_DELAY_MIN, SPIDER_DELAY_MAX))
            self._state["priority_done"] = True
            self._save_state()
            log.info("=== Phase 1 Complete ===")

        # ── Phase 2: Discovery (mở rộng theo hàng chờ) ──────────────────────
        if self.max_discovery is None or self.max_discovery > 0:
            limit_str = str(self.max_discovery) if self.max_discovery is not None else "Unlimited"
            log.info(f"=== Phase 2: Discovery (max {limit_str}) ===")
            count = 0
            while self._state["queue"]:
                if self.max_discovery is not None and count >= self.max_discovery:
                    break
                    
                url = self._state["queue"].pop(0)
                try:
                    if self._harvest_one(page, url):
                        count += 1
                except Exception as e:
                    log.error(f"Error harvesting {url}: {e}")
                    # Re-queue để thử lại sau
                    self._state["queue"].append(url)
                    self._save_state()
                time.sleep(random.uniform(SPIDER_DELAY_MIN, SPIDER_DELAY_MAX))
            log.info(f"=== Phase 2 Complete ({count} docs discovered) ===")

        page.close()
        log.info("Spider finished.")
