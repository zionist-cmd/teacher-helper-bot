from __future__ import annotations

import secrets
from dataclasses import dataclass
from html import escape
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.config import Settings
from app.db import Database
from app.keyboards import (
    BTN_EVENT_FORMATS,
    BTN_METHODICAL_ACTIVITY,
    BTN_METHODICAL_HELP,
    BTN_NORMATIVE,
    back_to_main_keyboard,
    event_format_keyboard,
    main_menu_keyboard,
    methodical_help_keyboard,
    normative_keyboard,
    question_actions_keyboard,
    retry_search_keyboard,
    search_result_keyboard,
    skip_school_keyboard,
)
from app.knowledge_base import (
    CATEGORY_TITLES,
    KnowledgeItem,
    QUESTION_TAGS,
    SUGGESTION_TAGS,
    get_category_items,
    get_methodical_faq,
    get_section_stats,
    search_all_items,
    search_items,
)
from app.services.exporter import ExportService
from app.states import RegistrationStates, SearchStates, SuggestionStates


@dataclass(slots=True)
class SearchSession:
    user_id: int
    query: str
    results: list[tuple[str, KnowledgeItem]]
    ask_category: str | None


def build_router(settings: Settings, database: Database, export_service: ExportService) -> Router:
    router = Router()
    event_format_titles = {
        "webinar": "Вебинар",
        "training": "Очный тренинг",
        "masterclass": "Мастер-класс",
    }
    search_sessions: dict[str, SearchSession] = {}
    screen_messages: dict[int, int] = {}
    section_emojis = {
        "normative": "📘",
        "methodical_help": "🧭",
        "event_formats": "🎤",
        "methodical_activity": "🧩",
    }

    def create_search_session(
        user_id: int,
        query: str,
        results: list[tuple[str, KnowledgeItem]],
        ask_category: str | None,
    ) -> str:
        if len(search_sessions) >= 200:
            oldest_key = next(iter(search_sessions))
            search_sessions.pop(oldest_key, None)
        session_id = secrets.token_hex(4)
        search_sessions[session_id] = SearchSession(
            user_id=user_id,
            query=query,
            results=results,
            ask_category=ask_category,
        )
        return session_id

    def build_menu_text(full_name: str | None = None) -> str:
        user_name = full_name or "коллега"
        stats = get_section_stats()
        lines = [
            f"Здравствуйте, <b>{escape(user_name)}</b>.",
            f"Сервис «Помощник Педагога» работает с <b>{settings.virtual_launch_date.strftime('%d.%m.%Y')}</b>.",
        ]
        lines.extend(
            [
                "",
                "<b>Статус сервиса</b>",
                f"• {section_emojis['normative']} Нормативы: {stats['normative_count']} материалов",
                f"• {section_emojis['methodical_help']} Методическая помощь: {stats['methodical_count']} материалов и {stats['faq_count']} FAQ",
                f"• {section_emojis['event_formats']} Идеи мероприятий: прием предложений открыт",
                f"• {section_emojis['methodical_activity']} Методическая деятельность: прием предложений открыт",
                "",
                "Выберите нужный раздел:",
            ]
        )
        return "\n".join(lines)

    async def delete_message_safe(bot: Bot, chat_id: int, message_id: int) -> None:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except (TelegramBadRequest, TelegramForbiddenError):
            return

    async def replace_chat_screen(
        message: Message,
        text: str,
        reply_markup=None,
        *,
        cleanup_current: bool = False,
    ) -> None:
        sent_message = await message.answer(text, reply_markup=reply_markup)
        previous_screen_id = screen_messages.get(message.chat.id)
        screen_messages[message.chat.id] = sent_message.message_id
        if previous_screen_id and previous_screen_id != sent_message.message_id:
            await delete_message_safe(message.bot, message.chat.id, previous_screen_id)
        if cleanup_current:
            await delete_message_safe(message.bot, message.chat.id, message.message_id)

    async def show_main_menu(
        message: Message,
        full_name: str | None = None,
        *,
        cleanup_current: bool = False,
    ) -> None:
        await replace_chat_screen(
            message,
            build_menu_text(full_name),
            reply_markup=main_menu_keyboard(),
            cleanup_current=cleanup_current,
        )

    async def edit_callback_screen(
        callback: CallbackQuery,
        text: str,
        reply_markup=None,
    ) -> None:
        try:
            await callback.message.edit_text(text, reply_markup=reply_markup)
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).casefold():
                raise
        screen_messages[callback.message.chat.id] = callback.message.message_id

    async def open_menu_section_message(
        message: Message,
        state: FSMContext,
        section: str,
    ) -> None:
        await state.clear()
        if section == "normative":
            await replace_chat_screen(
                message,
                "📘 <b>Нормативы</b>\n"
                "Здесь можно открыть подборку документов, выполнить поиск по ключевому слову или задать вопрос модератору.",
                reply_markup=normative_keyboard(),
                cleanup_current=True,
            )
            return
        if section == "methodical_help":
            await replace_chat_screen(
                message,
                "🧭 <b>Методическая помощь</b>\n"
                "Здесь доступны FAQ, поиск по базе знаний и отправка вопроса модератору.",
                reply_markup=methodical_help_keyboard(),
                cleanup_current=True,
            )
            return
        if section == "event_formats":
            await state.set_state(SuggestionStates.waiting_for_event_format)
            await replace_chat_screen(
                message,
                "🎤 Выберите формат мероприятия, который хотите предложить.",
                reply_markup=event_format_keyboard(),
                cleanup_current=True,
            )
            return
        await state.update_data(category="methodical_activity")
        await state.set_state(SuggestionStates.waiting_for_method_problem)
        await replace_chat_screen(
            message,
            "🧩 Шаг 1 из 3.\nОпишите проблему в методической деятельности, которую нужно решить.",
            reply_markup=back_to_main_keyboard(),
            cleanup_current=True,
        )

    async def open_menu_section_callback(
        callback: CallbackQuery,
        state: FSMContext,
        section: str,
    ) -> None:
        await state.clear()
        if section == "normative":
            await edit_callback_screen(
                callback,
                "📘 <b>Нормативы</b>\n"
                "Здесь можно открыть подборку документов, выполнить поиск по ключевому слову или задать вопрос модератору.",
                reply_markup=normative_keyboard(),
            )
            return
        if section == "methodical_help":
            await edit_callback_screen(
                callback,
                "🧭 <b>Методическая помощь</b>\n"
                "Здесь доступны FAQ, поиск по базе знаний и отправка вопроса модератору.",
                reply_markup=methodical_help_keyboard(),
            )
            return
        if section == "event_formats":
            await state.set_state(SuggestionStates.waiting_for_event_format)
            await edit_callback_screen(
                callback,
                "🎤 Выберите формат мероприятия, который хотите предложить.",
                reply_markup=event_format_keyboard(),
            )
            return
        await state.update_data(category="methodical_activity")
        await state.set_state(SuggestionStates.waiting_for_method_problem)
        await edit_callback_screen(
            callback,
            "🧩 Шаг 1 из 3.\nОпишите проблему в методической деятельности, которую нужно решить.",
            reply_markup=back_to_main_keyboard(),
        )

    async def get_user_profile(message: Message) -> dict:
        user = await database.get_user(message.from_user.id)
        if not user:
            raise RuntimeError("User profile is missing")
        return user

    async def notify_staff(
        bot: Bot,
        user: dict,
        category: str,
        tag: str,
        text: str,
        kind: str,
    ) -> None:
        school = user.get("school") or "не указан"
        username = f"@{user['username']}" if user.get("username") else "не указан"
        target_chat_ids = settings.questions_chat_ids if kind == "question" else settings.suggestions_chat_ids
        entry_label = "Вопрос" if kind == "question" else "Предложение"
        payload = "\n".join(
            [
                f"<b>Новая запись</b>: {entry_label}",
                f"<b>Категория:</b> {CATEGORY_TITLES[category]}",
                f"<b>Тег:</b> {tag}",
                f"<b>ФИО:</b> {escape(user['full_name'])}",
                f"<b>Школа:</b> {escape(school)}",
                f"<b>Username:</b> {escape(username)}",
                f"<b>Telegram ID:</b> <code>{user['telegram_id']}</code>",
                "",
                escape(text),
            ]
        )
        fallback_chat_ids = settings.admin_chat_ids
        for target_chat_id in target_chat_ids:
            try:
                await bot.send_message(target_chat_id, payload)
            except (TelegramBadRequest, TelegramForbiddenError):
                if target_chat_id in fallback_chat_ids:
                    raise
                fallback_payload = (
                    f"⚠️ Не удалось отправить уведомление в целевой чат <code>{target_chat_id}</code>.\n"
                    "Сообщение переадресовано резервным администраторам.\n\n"
                    f"{payload}"
                )
                for admin_chat_id in fallback_chat_ids:
                    await bot.send_message(admin_chat_id, fallback_payload)

    def build_search_text(session: SearchSession, offset: int) -> str:
        category, item = session.results[offset]
        emoji = section_emojis[category]
        return "\n".join(
            [
                f"🔎 <b>Поиск:</b> {escape(session.query)}",
                f"{emoji} <b>Результат {offset + 1} из {len(session.results)}</b> — {escape(CATEGORY_TITLES[category])}",
                "",
                f"<b>{escape(item.title)}</b>",
                escape(item.description),
            ]
        )

    async def send_search_card(message: Message, session_id: str, offset: int) -> None:
        session = search_sessions[session_id]
        _, item = session.results[offset]
        prev_callback = f"searchpage:{session_id}:{offset - 1}" if offset > 0 else None
        next_callback = (
            f"searchpage:{session_id}:{offset + 1}"
            if offset + 1 < len(session.results)
            else None
        )
        ask_callback = f"asksearch:{session_id}" if session.ask_category else None
        await message.answer(
            build_search_text(session, offset),
            reply_markup=search_result_keyboard(
                item_url=item.link,
                ask_callback=ask_callback,
                next_callback=next_callback,
                prev_callback=prev_callback,
            ),
        )

    async def edit_search_card(callback: CallbackQuery, session_id: str, offset: int) -> None:
        session = search_sessions[session_id]
        _, item = session.results[offset]
        prev_callback = f"searchpage:{session_id}:{offset - 1}" if offset > 0 else None
        next_callback = (
            f"searchpage:{session_id}:{offset + 1}"
            if offset + 1 < len(session.results)
            else None
        )
        ask_callback = f"asksearch:{session_id}" if session.ask_category else None
        await callback.message.edit_text(
            build_search_text(session, offset),
            reply_markup=search_result_keyboard(
                item_url=item.link,
                ask_callback=ask_callback,
                next_callback=next_callback,
                prev_callback=prev_callback,
            ),
        )

    async def present_search_results(
        message: Message,
        *,
        query: str,
        results: list[tuple[str, KnowledgeItem]],
        ask_category: str | None,
    ) -> None:
        session_id = create_search_session(
            user_id=message.from_user.id,
            query=query,
            results=results,
            ask_category=ask_category,
        )
        await send_search_card(message, session_id, 0)

    @router.message(CommandStart())
    async def command_start(message: Message, state: FSMContext) -> None:
        await state.clear()
        user = await database.get_user(message.from_user.id)
        if user:
            await show_main_menu(message, user["full_name"])
            return

        await message.answer(
            "Добро пожаловать в бот «Помощник Педагога» для организаций образования Казахстана.\n"
            "Для начала укажите ваше ФИО.",
        )
        await state.set_state(RegistrationStates.waiting_for_full_name)

    @router.message(RegistrationStates.waiting_for_full_name)
    async def save_full_name(message: Message, state: FSMContext) -> None:
        full_name = (message.text or "").strip()
        if len(full_name.split()) < 2:
            await message.answer("Введите ФИО полностью. Одного слова маловато даже для аналитики.")
            return

        await state.update_data(full_name=full_name)
        await state.set_state(RegistrationStates.waiting_for_school)
        await message.answer(
            "Укажите номер школы или нажмите «Пропустить».",
            reply_markup=skip_school_keyboard(),
        )

    @router.message(RegistrationStates.waiting_for_school)
    async def save_school(message: Message, state: FSMContext) -> None:
        school_input = (message.text or "").strip()
        school = None if school_input.casefold() == "пропустить" else school_input
        data = await state.get_data()
        full_name = data["full_name"]

        await database.upsert_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=full_name,
            school=school,
        )
        await state.clear()
        await show_main_menu(message, full_name, cleanup_current=True)

    @router.message(Command("menu"))
    async def command_menu(message: Message, state: FSMContext) -> None:
        await state.clear()
        user = await database.get_user(message.from_user.id)
        await show_main_menu(message, user["full_name"] if user else None, cleanup_current=True)

    @router.message(Command("search"))
    async def command_search(
        message: Message,
        state: FSMContext,
        command: CommandObject,
    ) -> None:
        await state.clear()
        query = (command.args or "").strip()
        if not query:
            await message.answer(
                "Использование: <code>/search отпуск</code>\n"
                "Команда ищет по разделам «Нормативы» и «Методическая помощь».",
                reply_markup=main_menu_keyboard(),
            )
            return

        results = search_all_items(query)
        if not results:
            await message.answer(
                "По общему поиску ничего не найдено. Попробуйте другое ключевое слово.",
                reply_markup=main_menu_keyboard(),
            )
            return

        await present_search_results(
            message,
            query=query,
            results=results,
            ask_category=None,
        )

    @router.message(Command("export"))
    async def command_export(message: Message, bot: Bot) -> None:
        if message.chat.id not in settings.admin_chat_ids:
            await message.answer("Команда доступна только администратору.")
            return

        export_path = await export_service.export_submissions(
            output_dir=settings.export_dir,
            kind="suggestion",
        )
        for admin_chat_id in settings.admin_chat_ids:
            await bot.send_document(
                chat_id=admin_chat_id,
                document=FSInputFile(export_path),
                caption="Выгрузка всех предложений.",
            )

    @router.message(Command("export_weekly"))
    async def command_export_weekly(message: Message, bot: Bot) -> None:
        if message.chat.id not in settings.admin_chat_ids:
            await message.answer("Команда доступна только администратору.")
            return

        export_path = await export_service.export_submissions(
            output_dir=settings.export_dir,
            days=7,
            kind="suggestion",
        )
        for admin_chat_id in settings.admin_chat_ids:
            await bot.send_document(
                chat_id=admin_chat_id,
                document=FSInputFile(export_path),
                caption="Выгрузка предложений за последние 7 дней.",
            )

    @router.message(Command("export_questions"))
    async def command_export_questions(message: Message, bot: Bot) -> None:
        if message.chat.id not in settings.admin_chat_ids:
            await message.answer("Команда доступна только администратору.")
            return

        export_path = await export_service.export_submissions(
            output_dir=settings.export_dir,
            kind="question",
        )
        for admin_chat_id in settings.admin_chat_ids:
            await bot.send_document(
                chat_id=admin_chat_id,
                document=FSInputFile(export_path),
                caption="Выгрузка всех вопросов.",
            )

    @router.message(Command("export_questions_weekly"))
    async def command_export_questions_weekly(message: Message, bot: Bot) -> None:
        if message.chat.id not in settings.admin_chat_ids:
            await message.answer("Команда доступна только администратору.")
            return

        export_path = await export_service.export_submissions(
            output_dir=settings.export_dir,
            days=7,
            kind="question",
        )
        for admin_chat_id in settings.admin_chat_ids:
            await bot.send_document(
                chat_id=admin_chat_id,
                document=FSInputFile(export_path),
                caption="Выгрузка вопросов за последние 7 дней.",
            )

    @router.message(F.text == BTN_NORMATIVE)
    async def open_normative(message: Message, state: FSMContext) -> None:
        await open_menu_section_message(message, state, "normative")

    @router.message(F.text == BTN_METHODICAL_HELP)
    async def open_methodical_help(message: Message, state: FSMContext) -> None:
        await open_menu_section_message(message, state, "methodical_help")

    @router.message(F.text == BTN_EVENT_FORMATS)
    async def open_event_formats(message: Message, state: FSMContext) -> None:
        await open_menu_section_message(message, state, "event_formats")

    @router.message(F.text == BTN_METHODICAL_ACTIVITY)
    async def open_methodical_activity(message: Message, state: FSMContext) -> None:
        await open_menu_section_message(message, state, "methodical_activity")

    @router.callback_query(F.data.startswith("menu:"))
    async def callback_open_menu_section(callback: CallbackQuery, state: FSMContext) -> None:
        _, section = callback.data.split(":", 1)
        await open_menu_section_callback(callback, state, section)
        await callback.answer()

    @router.callback_query(F.data.startswith("event_format:"))
    async def callback_event_format(callback: CallbackQuery, state: FSMContext) -> None:
        _, format_key = callback.data.split(":", 1)
        format_title = event_format_titles[format_key]
        await state.update_data(category="event_formats", event_format=format_title)
        await state.set_state(SuggestionStates.waiting_for_event_text)
        await edit_callback_screen(
            callback,
            "Опишите вашу идею, укажите целевую аудиторию и ожидаемый результат.\n"
            f"Выбранный формат: <b>{escape(format_title)}</b>.",
            reply_markup=back_to_main_keyboard(),
        )
        await callback.answer()

    @router.callback_query(F.data == "main_menu")
    async def callback_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        user = await database.get_user(callback.from_user.id)
        await edit_callback_screen(
            callback,
            build_menu_text(user["full_name"] if user else None),
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("popular:"))
    async def callback_popular(callback: CallbackQuery) -> None:
        _, category = callback.data.split(":", 1)
        items = get_category_items(category)
        text = [f"{section_emojis[category]} <b>Подборка материалов</b>:"]
        for item in items[:3]:
            text.append(
                f"• <b>{escape(item.title)}</b>\n"
                f"{escape(item.description)}\n"
                f"<a href=\"{escape(item.link)}\">Открыть материал</a>"
            )
        await edit_callback_screen(
            callback,
            "\n\n".join(text),
            reply_markup=question_actions_keyboard(category),
        )
        await callback.answer()

    @router.callback_query(F.data == "faq:methodical_help")
    async def callback_faq(callback: CallbackQuery) -> None:
        lines = ["🧭 <b>Частые вопросы</b>:"]
        for question, answer in get_methodical_faq():
            lines.append(f"• <b>{escape(question)}</b>\n{escape(answer)}")
        await edit_callback_screen(
            callback,
            "\n\n".join(lines),
            reply_markup=question_actions_keyboard("methodical_help"),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("search:"))
    async def callback_search(callback: CallbackQuery, state: FSMContext) -> None:
        _, category = callback.data.split(":", 1)
        await state.update_data(category=category)
        await state.set_state(SearchStates.waiting_for_query)
        await edit_callback_screen(
            callback,
            f"Введите ключевое слово для раздела «{CATEGORY_TITLES[category]}».",
            reply_markup=back_to_main_keyboard(),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("searchpage:"))
    async def callback_search_page(callback: CallbackQuery) -> None:
        _, session_id, offset_raw = callback.data.split(":", 2)
        session = search_sessions.get(session_id)
        if session is None:
            await callback.answer("Сессия поиска устарела. Запустите поиск заново.", show_alert=True)
            return
        if session.user_id != callback.from_user.id:
            await callback.answer("Это не ваш поиск.", show_alert=True)
            return
        offset = int(offset_raw)
        if offset < 0 or offset >= len(session.results):
            await callback.answer("Больше результатов нет.")
            return
        await edit_search_card(callback, session_id, offset)
        await callback.answer()

    @router.callback_query(F.data.startswith("asksearch:"))
    async def callback_ask_from_search(callback: CallbackQuery, state: FSMContext) -> None:
        _, session_id = callback.data.split(":", 1)
        session = search_sessions.get(session_id)
        if session is None or session.ask_category is None:
            await callback.answer("Запустите поиск заново.", show_alert=True)
            return
        if session.user_id != callback.from_user.id:
            await callback.answer("Это не ваш поиск.", show_alert=True)
            return
        await state.update_data(category=session.ask_category)
        await state.set_state(SearchStates.waiting_for_custom_question)
        await edit_callback_screen(
            callback,
            f"Напишите ваш вопрос по теме «{CATEGORY_TITLES[session.ask_category]}».",
            reply_markup=back_to_main_keyboard(),
        )
        await callback.answer()

    @router.message(SearchStates.waiting_for_query)
    async def handle_search(message: Message, state: FSMContext) -> None:
        query = (message.text or "").strip()
        data = await state.get_data()
        category = data["category"]
        results = [(category, item) for item in search_items(category, query)]
        await state.clear()

        if not results:
            await message.answer(
                "По запросу ничего не нашлось. Да, база не умеет читать мысли.\n"
                "Попробуйте другой запрос или отправьте вопрос модератору.",
                reply_markup=retry_search_keyboard(category),
            )
            return

        await present_search_results(
            message,
            query=query,
            results=results,
            ask_category=category,
        )

    @router.callback_query(F.data.startswith("ask:"))
    async def callback_ask_question(callback: CallbackQuery, state: FSMContext) -> None:
        _, category = callback.data.split(":", 1)
        await state.update_data(category=category)
        await state.set_state(SearchStates.waiting_for_custom_question)
        await edit_callback_screen(
            callback,
            f"Напишите ваш вопрос по теме «{CATEGORY_TITLES[category]}».",
            reply_markup=back_to_main_keyboard(),
        )
        await callback.answer()

    @router.message(SearchStates.waiting_for_custom_question)
    async def handle_custom_question(message: Message, state: FSMContext, bot: Bot) -> None:
        text = (message.text or "").strip()
        if len(text) < 10:
            await message.answer("Сформулируйте вопрос чуть подробнее, чтобы его можно было корректно направить специалисту.")
            return

        data = await state.get_data()
        category = data["category"]
        tag = QUESTION_TAGS[category]
        user = await get_user_profile(message)

        await database.create_submission(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=user["full_name"],
            school=user.get("school"),
            category=category,
            tag=tag,
            text=text,
            kind="question",
        )
        await notify_staff(bot, user, category, tag, text, "question")
        await state.clear()
        await message.answer(
            f"Спасибо. Ваш вопрос в категории «{CATEGORY_TITLES[category]}» принят и направлен модератору.",
            reply_markup=back_to_main_keyboard(),
        )

    @router.message(SuggestionStates.waiting_for_event_text)
    async def handle_event_suggestion(message: Message, state: FSMContext, bot: Bot) -> None:
        text = (message.text or "").strip()
        if len(text) < 15:
            await message.answer("Добавьте деталей: цель, аудиторию и ожидаемый результат. Иначе идея звучит как черновик черновика.")
            return

        data = await state.get_data()
        category = "event_formats"
        tag = SUGGESTION_TAGS[category]
        format_title = data["event_format"]
        user = await get_user_profile(message)
        payload = f"Формат: {format_title}\n{text}"

        await database.create_submission(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=user["full_name"],
            school=user.get("school"),
            category=category,
            tag=tag,
            text=payload,
            kind="suggestion",
        )
        await notify_staff(bot, user, category, tag, payload, "suggestion")
        await state.clear()
        await message.answer(
            f"Спасибо! Ваше предложение в категории «{CATEGORY_TITLES[category]}» принято и будет рассмотрено методическим советом.",
            reply_markup=back_to_main_keyboard(),
        )

    @router.message(SuggestionStates.waiting_for_method_problem)
    async def handle_method_problem(message: Message, state: FSMContext) -> None:
        problem = (message.text or "").strip()
        if len(problem) < 10:
            await message.answer("Опишите проблему чуть конкретнее. Пока это выглядит как заголовок без содержания.")
            return

        await state.update_data(problem=problem)
        await state.set_state(SuggestionStates.waiting_for_method_solution)
        await message.answer(
            "Шаг 2 из 3.\nОпишите предлагаемое решение или улучшение.",
            reply_markup=back_to_main_keyboard(),
        )

    @router.message(SuggestionStates.waiting_for_method_solution)
    async def handle_method_solution(message: Message, state: FSMContext) -> None:
        solution = (message.text or "").strip()
        if len(solution) < 10:
            await message.answer("Нужно чуть больше конкретики по решению. Пока пользы меньше, чем текста.")
            return

        await state.update_data(solution=solution)
        await state.set_state(SuggestionStates.waiting_for_method_result)
        await message.answer(
            "Шаг 3 из 3.\nКакой ожидаемый результат или эффект вы хотите получить?",
            reply_markup=back_to_main_keyboard(),
        )

    @router.message(SuggestionStates.waiting_for_method_result)
    async def handle_method_result(message: Message, state: FSMContext, bot: Bot) -> None:
        result = (message.text or "").strip()
        if len(result) < 10:
            await message.answer("Опишите ожидаемый результат чуть подробнее. Одной общей фразой тут не отделаться.")
            return

        data = await state.get_data()
        category = "methodical_activity"
        tag = SUGGESTION_TAGS[category]
        user = await get_user_profile(message)
        payload = (
            f"Проблема: {data['problem']}\n"
            f"Предлагаемое решение: {data['solution']}\n"
            f"Ожидаемый результат: {result}"
        )

        await database.create_submission(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=user["full_name"],
            school=user.get("school"),
            category=category,
            tag=tag,
            text=payload,
            kind="suggestion",
        )
        await notify_staff(bot, user, category, tag, payload, "suggestion")
        await state.clear()
        await message.answer(
            f"Спасибо! Ваше предложение в категории «{CATEGORY_TITLES[category]}» принято и будет рассмотрено методическим советом.",
            reply_markup=back_to_main_keyboard(),
        )

    @router.message()
    async def fallback(message: Message) -> None:
        await message.answer(
            "Используйте кнопки меню или команду /start. Свободный текст без контекста бот пока не классифицирует магией.",
            reply_markup=main_menu_keyboard(),
        )

    return router
