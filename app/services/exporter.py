from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from app.db import Database, ExportRow


class ExportService:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def export_submissions(
        self,
        output_dir: Path,
        days: int | None = None,
        kind: str | None = None,
    ) -> Path:
        rows = await self.database.export_filtered_rows(days=days, kind=kind)
        output_dir.mkdir(parents=True, exist_ok=True)

        scope = kind or "submissions"
        filename = f"{scope}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path = output_dir / filename
        await asyncio.to_thread(self._write_workbook, rows, path)
        return path

    def _write_workbook(self, rows: list[ExportRow], path: Path) -> None:
        workbook = Workbook()
        worksheet = workbook.active
        if path.stem.startswith("suggestion_"):
            worksheet.title = "Предложения"
        elif path.stem.startswith("question_"):
            worksheet.title = "Вопросы"
        else:
            worksheet.title = "Предложения и вопросы"

        headers = [
            "Дата",
            "Telegram ID",
            "Username",
            "ФИО",
            "Школа",
            "Категория",
            "Тег",
            "Тип",
            "Текст",
        ]
        worksheet.append(headers)
        for cell in worksheet[1]:
            cell.font = Font(bold=True)

        for row in rows:
            worksheet.append(
                [
                    row.created_at,
                    row.telegram_id,
                    row.username or "",
                    row.full_name,
                    row.school or "",
                    row.category,
                    row.tag,
                    row.kind,
                    row.text,
                ]
            )

        worksheet.freeze_panes = "A2"
        worksheet.column_dimensions["A"].width = 22
        worksheet.column_dimensions["B"].width = 14
        worksheet.column_dimensions["C"].width = 20
        worksheet.column_dimensions["D"].width = 28
        worksheet.column_dimensions["E"].width = 16
        worksheet.column_dimensions["F"].width = 24
        worksheet.column_dimensions["G"].width = 18
        worksheet.column_dimensions["H"].width = 12
        worksheet.column_dimensions["I"].width = 80

        workbook.save(path)
