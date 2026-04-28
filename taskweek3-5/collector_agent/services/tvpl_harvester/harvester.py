"""
tvpl_harvester/harvester.py
============================
Facade class — điểm duy nhất bên ngoài cần gọi.
Orchestrator hoặc API endpoint chỉ cần import và gọi:

    from collector_agent.services.tvpl_harvester import TVPLHarvester
    TVPLHarvester(output_dir=..., state_file=...).run(max_discovery=20)
"""

import logging
from pathlib import Path

from .browser import TVPLBrowser
from .spider import TVPLSpider

log = logging.getLogger("TVPL.Harvester")


class TVPLHarvester:
    """
    Facade tích hợp Browser + Spider.

    Args:
        output_dir:    Nơi lưu file Markdown đã cào.
        state_file:    File JSON lưu tiến độ (resume-safe).
        headless:      True = chạy ẩn browser (production), False = debug.
    """

    def __init__(
        self,
        output_dir: Path,
        state_file: Path,
        headless: bool = True,
    ):
        self.output_dir = output_dir
        self.state_file = state_file
        self.headless = headless

    def run(self, max_discovery: int | None = 0) -> list[Path]:
        """
        Chạy đầy đủ: Phase 1 (7 priority) → Phase 2 (discovery).

        Args:
            max_discovery: Số tài liệu tối đa ở Phase 2. 0 = chỉ chạy Phase 1. None = cào vô hạn.

        Returns:
            Danh sách Path các file Markdown đã tạo mới trong lần chạy này.
        """
        spider = TVPLSpider(
            output_dir=self.output_dir,
            state_file=self.state_file,
            max_discovery=max_discovery,
        )

        before = set(self.output_dir.glob("*.md"))

        with TVPLBrowser(headless=self.headless) as context:
            spider.run(context)

        after = set(self.output_dir.glob("*.md"))
        new_files = sorted(after - before)
        log.info(f"Harvester done. New files: {len(new_files)}")
        return new_files
