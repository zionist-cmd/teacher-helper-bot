from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import FSInputFile

from app.config import Settings
from app.services.exporter import ExportService


logger = logging.getLogger(__name__)


class WeeklyExportService:
    def __init__(self, bot: Bot, export_service: ExportService, settings: Settings) -> None:
        self.bot = bot
        self.export_service = export_service
        self.settings = settings
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if not self.settings.weekly_export_enabled:
            return
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="weekly-export")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        while True:
            delay = self._seconds_until_next_run()
            logger.info("Weekly export scheduled in %.0f seconds", delay)
            await asyncio.sleep(delay)
            await self._send_weekly_export()

    def _seconds_until_next_run(self) -> float:
        now = datetime.now(self.settings.timezone)
        run_at = now.replace(
            hour=self.settings.weekly_export_hour,
            minute=self.settings.weekly_export_minute,
            second=0,
            microsecond=0,
        )
        days_ahead = (self.settings.weekly_export_weekday - now.weekday()) % 7
        if days_ahead == 0 and run_at <= now:
            days_ahead = 7
        target = run_at + timedelta(days=days_ahead)
        return max((target - now).total_seconds(), 1.0)

    async def _send_weekly_export(self) -> None:
        try:
            path = await self.export_service.export_submissions(
                output_dir=self.settings.export_dir,
                days=7,
                kind="suggestion",
            )
            for admin_chat_id in self.settings.admin_chat_ids:
                await self.bot.send_document(
                    chat_id=admin_chat_id,
                    document=FSInputFile(path),
                    caption="Автоматическая недельная выгрузка предложений.",
                )
            logger.info("Weekly export sent to admin chat")
        except Exception:
            logger.exception("Weekly export failed")
