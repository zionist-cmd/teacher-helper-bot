from __future__ import annotations

import asyncio
import csv
import io
import logging
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout

from app.config import Settings
from app.knowledge_base import (
    KnowledgeItem,
    replace_category_items,
    replace_methodical_faq,
)


logger = logging.getLogger(__name__)
ITEM_FIELDS = {"title", "description", "link", "keywords"}
FAQ_FIELDS = {"question", "answer"}


class ContentLoaderService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def load(self) -> None:
        jobs = []
        if self.settings.normative_sheet_url:
            jobs.append(self._load_items("normative", self.settings.normative_sheet_url))
        if self.settings.methodical_sheet_url:
            jobs.append(self._load_items("methodical_help", self.settings.methodical_sheet_url))
        if self.settings.faq_sheet_url:
            jobs.append(self._load_faq(self.settings.faq_sheet_url))

        if not jobs:
            return

        results = await asyncio.gather(*jobs, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error("External content loading failed: %s", result, exc_info=result)

    async def _load_items(self, category: str, url: str) -> None:
        text = await self._fetch_csv(url)
        rows = csv.DictReader(io.StringIO(text))
        self._validate_columns(rows.fieldnames, ITEM_FIELDS, url)
        items: list[KnowledgeItem] = []
        for row in rows:
            title = (row.get("title") or "").strip()
            description = (row.get("description") or "").strip()
            link = (row.get("link") or "").strip()
            keywords_raw = (row.get("keywords") or "").replace(";", ",")
            keywords = tuple(
                keyword.strip()
                for keyword in keywords_raw.split(",")
                if keyword.strip()
            )
            if not title or not description or not link:
                continue
            if not self._is_safe_external_link(link):
                logger.warning("Skipped invalid external link in %s: %s", url, link)
                continue
            items.append(
                KnowledgeItem(
                    title=title,
                    description=description,
                    link=link,
                    keywords=keywords,
                )
            )

        if items:
            replace_category_items(category, items)
            logger.info("Loaded %s external items for %s", len(items), category)

    async def _load_faq(self, url: str) -> None:
        text = await self._fetch_csv(url)
        rows = csv.DictReader(io.StringIO(text))
        self._validate_columns(rows.fieldnames, FAQ_FIELDS, url)
        items: list[tuple[str, str]] = []
        for row in rows:
            question = (row.get("question") or "").strip()
            answer = (row.get("answer") or "").strip()
            if question and answer:
                items.append((question, answer))

        if items:
            replace_methodical_faq(items)
            logger.info("Loaded %s external FAQ items", len(items))

    async def _fetch_csv(self, url: str) -> str:
        timeout = ClientTimeout(total=20)
        async with ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text(encoding="utf-8-sig")

    @staticmethod
    def _validate_columns(
        fieldnames: list[str] | None,
        required_fields: set[str],
        source_url: str,
    ) -> None:
        actual_fields = {field.strip() for field in (fieldnames or []) if field and field.strip()}
        missing_fields = required_fields - actual_fields
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"CSV schema mismatch for {source_url}. Missing columns: {missing}")

    @staticmethod
    def _is_safe_external_link(link: str) -> bool:
        parsed = urlparse(link)
        return parsed.scheme == "https" and bool(parsed.netloc)
