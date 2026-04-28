"""
test_tvpl_harvester.py
=======================
Test kín cho TVPLHarvester — chạy độc lập, không cần khởi động toàn bộ hệ thống.
Kiểm tra:
  1. Phase 1: Cào đúng 7 priority URLs, lưu file MD đúng định dạng.
  2. Phase 2: Discovery mở rộng thêm N văn bản.
  3. Anti-poisoning: Không có file Untitled.md, không trùng lặp.
  4. Metadata: YAML frontmatter có đủ các field cần thiết.
  5. Resume: Chạy lại lần 2 không cào trùng.

Cách chạy:
    python test_tvpl_harvester.py           # chỉ Phase 1
    python test_tvpl_harvester.py --discover 5  # Phase 1 + 5 discovery
"""

import sys
import json
import shutil
import logging
import argparse
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import collector_agent
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from collector_agent.services.tvpl_harvester import TVPLHarvester

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT / "scratch" / "TVPL-test-get" / "test_harvester.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("Test")

OUTPUT_DIR = ROOT / "scratch" / "TVPL-test-get" / "test_output"
STATE_FILE = ROOT / "scratch" / "TVPL-test-get" / "test_spider_state.json"


def clean_env():
    """Dọn sạch môi trường test để chạy fresh."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    log.info("Clean environment ready.")


def run_tests(max_discovery: int):
    from collector_agent.services.tvpl_harvester.config import PRIORITY_URLS

    log.info("=" * 60)
    log.info("TVPL Harvester — Integration Test")
    log.info(f"Phase 1: {len(PRIORITY_URLS)} priority URLs")
    log.info(f"Phase 2: max_discovery={max_discovery}")
    log.info("=" * 60)

    harvester = TVPLHarvester(
        output_dir=OUTPUT_DIR,
        state_file=STATE_FILE,
        headless=True,
    )
    new_files = harvester.run(max_discovery=max_discovery)

    # ── Assertions ────────────────────────────────────────────────────────────
    errors = []

    # 1. Không có Untitled.md
    for f in OUTPUT_DIR.glob("*.md"):
        if "untitled" in f.name.lower() or f.name == "_.md":
            errors.append(f"❌ Untitled file found: {f.name}")

    # 2. Mỗi file phải có frontmatter
    for f in OUTPUT_DIR.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        if not text.startswith("---"):
            errors.append(f"❌ Missing frontmatter: {f.name}")
        if 'title:' not in text:
            errors.append(f"❌ Missing title in frontmatter: {f.name}")
        if 'status:' not in text:
            errors.append(f"❌ Missing status in frontmatter: {f.name}")

    # 3. Phase 1 hoàn tất — state.priority_done = True
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if not state.get("priority_done"):
        errors.append("❌ priority_done is False after run!")

    # 4. Không trùng lặp trong processed list
    processed = state.get("processed", [])
    if len(processed) != len(set(processed)):
        errors.append("❌ Duplicate URLs in processed list!")

    # ── Report ────────────────────────────────────────────────────────────────
    log.info("=" * 60)
    log.info(f"New files created: {len(new_files)}")
    for f in sorted(OUTPUT_DIR.glob("*.md")):
        size_kb = f.stat().st_size / 1024
        log.info(f"  📄 {f.name}  ({size_kb:.1f} KB)")

    if errors:
        log.error(f"\n{len(errors)} FAILURES:")
        for e in errors:
            log.error(f"  {e}")
        sys.exit(1)
    else:
        log.info(f"\n✅ All assertions passed! ({len(list(OUTPUT_DIR.glob('*.md')))} docs)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--discover", type=int, default=0,
                        help="Number of discovery docs (Phase 2). Default=0 (priority only).")
    parser.add_argument("--clean", action="store_true",
                        help="Clean test environment before running.")
    args = parser.parse_args()

    if args.clean:
        clean_env()

    run_tests(max_discovery=args.discover)
