import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


PLACEHOLDER_CHAT_IDS = {"123456789", "0"}
PLACEHOLDER_BOT_TOKENS = {
    "your_telegram_bot_token",
    "replace_me",
    "changeme",
    "...",
}
ALLOWED_SHEET_HOSTS = {"docs.google.com"}


@dataclass(slots=True)
class Settings:
    bot_token: str
    admin_chat_id: int
    questions_chat_id: int
    suggestions_chat_id: int
    db_path: Path
    export_dir: Path
    demo_mode: bool
    virtual_launch_date: date
    timezone: ZoneInfo
    weekly_export_enabled: bool
    weekly_export_weekday: int
    weekly_export_hour: int
    weekly_export_minute: int
    startup_delay_seconds: int
    normative_sheet_url: str | None
    methodical_sheet_url: str | None
    faq_sheet_url: str | None


def default_virtual_launch_date() -> date:
    return date(2025, 9, 1)


def parse_bool(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "yes", "y", "on"}


def parse_bot_token(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise RuntimeError("BOT_TOKEN is not set")
    if cleaned.casefold() in PLACEHOLDER_BOT_TOKENS or ":" not in cleaned:
        raise RuntimeError("BOT_TOKEN contains a placeholder or invalid value")
    return cleaned


def parse_chat_id(name: str, value: str, *, default: int | None = None) -> int:
    cleaned = value.strip()
    if not cleaned:
        if default is None:
            raise RuntimeError(f"{name} is not set")
        return default
    if cleaned in PLACEHOLDER_CHAT_IDS:
        raise RuntimeError(f"{name} still contains the example placeholder")
    try:
        chat_id = int(cleaned)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer chat id") from exc
    if chat_id == 0:
        raise RuntimeError(f"{name} must not be 0")
    return chat_id


def parse_optional_sheet_url(name: str, value: str) -> str | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    parsed = urlparse(cleaned)
    query = parsed.query.casefold()
    if parsed.scheme != "https":
        raise RuntimeError(f"{name} must use https")
    if parsed.netloc not in ALLOWED_SHEET_HOSTS:
        raise RuntimeError(f"{name} must point to a published Google Sheets CSV URL")
    if "/spreadsheets/" not in parsed.path:
        raise RuntimeError(f"{name} must point to a Google Sheets document")
    if "format=csv" not in query and "output=csv" not in query:
        raise RuntimeError(f"{name} must be a CSV export URL")
    return cleaned


def default_db_path() -> str:
    if os.getenv("AMVERA", "").strip() == "1":
        return "/data/bot.sqlite3"
    return "bot.sqlite3"


def default_export_dir() -> str:
    if os.getenv("AMVERA", "").strip() == "1":
        return "/data/exports"
    return "exports"


def default_startup_delay_seconds() -> str:
    if os.getenv("AMVERA", "").strip() == "1":
        return "5"
    return "0"


def load_settings() -> Settings:
    load_dotenv()

    bot_token_raw = os.getenv("BOT_TOKEN", "").strip()
    admin_chat_id_raw = os.getenv("ADMIN_CHAT_ID", "").strip()
    questions_chat_id_raw = os.getenv("QUESTIONS_CHAT_ID", "").strip()
    suggestions_chat_id_raw = os.getenv("SUGGESTIONS_CHAT_ID", "").strip()
    db_path_raw = os.getenv("DB_PATH", default_db_path()).strip()
    export_dir_raw = os.getenv("EXPORT_DIR", default_export_dir()).strip()
    demo_mode_raw = os.getenv("DEMO_MODE", "false").strip()
    virtual_launch_date_raw = os.getenv("VIRTUAL_LAUNCH_DATE", "").strip()
    timezone_raw = os.getenv("BOT_TIMEZONE", "Asia/Qyzylorda").strip()
    weekly_export_enabled_raw = os.getenv("WEEKLY_EXPORT_ENABLED", "false").strip()
    weekly_export_weekday_raw = os.getenv("WEEKLY_EXPORT_WEEKDAY", "0").strip()
    weekly_export_hour_raw = os.getenv("WEEKLY_EXPORT_HOUR", "9").strip()
    weekly_export_minute_raw = os.getenv("WEEKLY_EXPORT_MINUTE", "0").strip()
    startup_delay_seconds_raw = os.getenv(
        "STARTUP_DELAY_SECONDS",
        default_startup_delay_seconds(),
    ).strip()
    normative_sheet_url_raw = os.getenv("NORMATIVE_SHEET_CSV_URL", "").strip()
    methodical_sheet_url_raw = os.getenv("METHODICAL_SHEET_CSV_URL", "").strip()
    faq_sheet_url_raw = os.getenv("FAQ_SHEET_CSV_URL", "").strip()

    virtual_launch_date = (
        date.fromisoformat(virtual_launch_date_raw)
        if virtual_launch_date_raw
        else default_virtual_launch_date()
    )
    bot_token = parse_bot_token(bot_token_raw)
    admin_chat_id = parse_chat_id("ADMIN_CHAT_ID", admin_chat_id_raw)
    questions_chat_id = parse_chat_id(
        "QUESTIONS_CHAT_ID",
        questions_chat_id_raw,
        default=admin_chat_id,
    )
    suggestions_chat_id = parse_chat_id(
        "SUGGESTIONS_CHAT_ID",
        suggestions_chat_id_raw,
        default=admin_chat_id,
    )

    return Settings(
        bot_token=bot_token,
        admin_chat_id=admin_chat_id,
        questions_chat_id=questions_chat_id,
        suggestions_chat_id=suggestions_chat_id,
        db_path=Path(db_path_raw),
        export_dir=Path(export_dir_raw),
        demo_mode=parse_bool(demo_mode_raw),
        virtual_launch_date=virtual_launch_date,
        timezone=ZoneInfo(timezone_raw),
        weekly_export_enabled=parse_bool(weekly_export_enabled_raw),
        weekly_export_weekday=int(weekly_export_weekday_raw),
        weekly_export_hour=int(weekly_export_hour_raw),
        weekly_export_minute=int(weekly_export_minute_raw),
        startup_delay_seconds=max(int(startup_delay_seconds_raw), 0),
        normative_sheet_url=parse_optional_sheet_url(
            "NORMATIVE_SHEET_CSV_URL",
            normative_sheet_url_raw,
        ),
        methodical_sheet_url=parse_optional_sheet_url(
            "METHODICAL_SHEET_CSV_URL",
            methodical_sheet_url_raw,
        ),
        faq_sheet_url=parse_optional_sheet_url("FAQ_SHEET_CSV_URL", faq_sheet_url_raw),
    )
