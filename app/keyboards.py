from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


BTN_NORMATIVE = "📘 Нормативы"
BTN_METHODICAL_HELP = "🧭 Методическая помощь"
BTN_EVENT_FORMATS = "🎤 Форматы мероприятий"
BTN_METHODICAL_ACTIVITY = "🧩 Методическая деятельность"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=BTN_NORMATIVE, callback_data="menu:normative"),
                InlineKeyboardButton(
                    text=BTN_METHODICAL_HELP,
                    callback_data="menu:methodical_help",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=BTN_EVENT_FORMATS,
                    callback_data="menu:event_formats",
                ),
                InlineKeyboardButton(
                    text=BTN_METHODICAL_ACTIVITY,
                    callback_data="menu:methodical_activity",
                ),
            ],
        ]
    )


def skip_school_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def question_actions_keyboard(category: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Поиск по ключевому слову",
                    callback_data=f"search:{category}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Задать свой вопрос",
                    callback_data=f"ask:{category}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Главное меню",
                    callback_data="main_menu",
                )
            ],
        ]
    )


def normative_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Популярные документы",
                    callback_data="popular:normative",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Поиск по ключевому слову",
                    callback_data="search:normative",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Задать свой вопрос",
                    callback_data="ask:normative",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Главное меню",
                    callback_data="main_menu",
                )
            ],
        ]
    )


def methodical_help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Частые вопросы",
                    callback_data="faq:methodical_help",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Поиск по ключевому слову",
                    callback_data="search:methodical_help",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Задать свой вопрос",
                    callback_data="ask:methodical_help",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Главное меню",
                    callback_data="main_menu",
                )
            ],
        ]
    )


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )


def event_format_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Вебинар", callback_data="event_format:webinar")],
            [InlineKeyboardButton(text="Очный тренинг", callback_data="event_format:training")],
            [InlineKeyboardButton(text="Мастер-класс", callback_data="event_format:masterclass")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")],
        ]
    )


def retry_search_keyboard(category: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Попробовать другой запрос",
                    callback_data=f"search:{category}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Задать свой вопрос",
                    callback_data=f"ask:{category}",
                )
            ],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")],
        ]
    )


def search_result_keyboard(
    *,
    item_url: str,
    ask_callback: str | None = None,
    next_callback: str | None = None,
    prev_callback: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="Открыть", url=item_url)]
    ]
    nav_row: list[InlineKeyboardButton] = []
    if prev_callback:
        nav_row.append(InlineKeyboardButton(text="Назад", callback_data=prev_callback))
    if next_callback:
        nav_row.append(InlineKeyboardButton(text="Еще варианты", callback_data=next_callback))
    if nav_row:
        rows.append(nav_row)
    if ask_callback:
        rows.append([InlineKeyboardButton(text="Задать вопрос", callback_data=ask_callback)])
    rows.append([InlineKeyboardButton(text="Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
