from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiosqlite


@dataclass(slots=True)
class ExportRow:
    created_at: str
    telegram_id: int
    username: str | None
    full_name: str
    school: str | None
    category: str
    tag: str
    text: str
    kind: str


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.connection = await aiosqlite.connect(self.path)
        self.connection.row_factory = aiosqlite.Row

    async def close(self) -> None:
        if self.connection is not None:
            await self.connection.close()

    async def init_schema(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT NOT NULL,
            school TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT NOT NULL,
            school TEXT,
            category TEXT NOT NULL,
            tag TEXT NOT NULL,
            text TEXT NOT NULL,
            kind TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.executescript(query)
        await self.connection.commit()

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        cursor = await self.connection.execute(
            """
            SELECT telegram_id, username, full_name, school, created_at
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None

    async def upsert_user(
        self,
        telegram_id: int,
        username: str | None,
        full_name: str,
        school: str | None,
    ) -> None:
        await self.connection.execute(
            """
            INSERT INTO users (telegram_id, username, full_name, school)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                school = excluded.school
            """,
            (telegram_id, username, full_name, school),
        )
        await self.connection.commit()

    async def create_submission(
        self,
        telegram_id: int,
        username: str | None,
        full_name: str,
        school: str | None,
        category: str,
        tag: str,
        text: str,
        kind: str,
        created_at: str | None = None,
    ) -> None:
        if created_at is None:
            await self.connection.execute(
                """
                INSERT INTO submissions (
                    telegram_id, username, full_name, school, category, tag, text, kind
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (telegram_id, username, full_name, school, category, tag, text, kind),
            )
        else:
            await self.connection.execute(
                """
                INSERT INTO submissions (
                    telegram_id, username, full_name, school, category, tag, text, kind, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (telegram_id, username, full_name, school, category, tag, text, kind, created_at),
            )
        await self.connection.commit()

    async def submissions_count(self) -> int:
        cursor = await self.connection.execute("SELECT COUNT(*) AS total FROM submissions")
        row = await cursor.fetchone()
        await cursor.close()
        return int(row["total"])

    async def export_rows(self, days: int | None = None) -> list[ExportRow]:
        return await self.export_filtered_rows(days=days)

    async def export_filtered_rows(
        self,
        days: int | None = None,
        kind: str | None = None,
    ) -> list[ExportRow]:
        query = """
        SELECT created_at, telegram_id, username, full_name, school, category, tag, text, kind
        FROM submissions
        """
        conditions: list[str] = []
        params_list: list[Any] = []
        if days is not None:
            threshold = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            conditions.append("created_at >= ?")
            params_list.append(threshold)
        if kind is not None:
            conditions.append("kind = ?")
            params_list.append(kind)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"
        params = tuple(params_list)
        cursor = await self.connection.execute(query, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return [ExportRow(**dict(row)) for row in rows]
