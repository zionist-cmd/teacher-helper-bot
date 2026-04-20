import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.config import load_settings
from app.db import Database
from app.handlers import build_router
from app.services.content_loader import ContentLoaderService
from app.services.exporter import ExportService
from app.services.history_seed import HistorySeedService
from app.services.weekly_export import WeeklyExportService


async def validate_runtime_configuration(bot: Bot, settings) -> None:
    chat_targets = {
        "ADMIN_CHAT_IDS": settings.admin_chat_ids,
        "QUESTIONS_CHAT_IDS": settings.questions_chat_ids,
        "SUGGESTIONS_CHAT_IDS": settings.suggestions_chat_ids,
    }
    checked_chat_ids: set[int] = set()
    for label, chat_ids in chat_targets.items():
        for chat_id in chat_ids:
            if chat_id in checked_chat_ids:
                continue
            try:
                await bot.get_chat(chat_id)
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                raise RuntimeError(
                    f"{label} points to an unavailable chat: {chat_id}. "
                    "Add the bot to that chat and verify the id in secrets."
                ) from exc
            checked_chat_ids.add(chat_id)

    if set(settings.questions_chat_ids) == set(settings.admin_chat_ids):
        logging.warning("QUESTIONS_CHAT_IDS is not separated from ADMIN_CHAT_IDS")
    if set(settings.suggestions_chat_ids) == set(settings.admin_chat_ids):
        logging.warning("SUGGESTIONS_CHAT_IDS is not separated from ADMIN_CHAT_IDS")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    settings = load_settings()
    content_loader = ContentLoaderService(settings)
    await content_loader.load()

    database = Database(settings.db_path)
    await database.connect()
    await database.init_schema()
    if settings.demo_mode:
        history_seed_service = HistorySeedService(database)
        await history_seed_service.ensure_seeded(settings.virtual_launch_date)

    if settings.startup_delay_seconds:
        logging.info("Startup delay enabled for %s seconds", settings.startup_delay_seconds)
        await asyncio.sleep(settings.startup_delay_seconds)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await validate_runtime_configuration(bot, settings)
    dispatcher = Dispatcher()
    export_service = ExportService(database)
    weekly_export_service = WeeklyExportService(bot, export_service, settings)

    dispatcher.include_router(build_router(settings, database, export_service))

    try:
        weekly_export_service.start()
        await dispatcher.start_polling(bot)
    finally:
        await weekly_export_service.stop()
        await database.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
