from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


TAG_NORMATIVE = "#норматив"
TAG_METHOD_HELP = "#метод_помощь"
TAG_EVENT = "#мероприятие"
TAG_METHOD_IDEA = "#идея_методика"


@dataclass(frozen=True, slots=True)
class KnowledgeItem:
    title: str
    description: str
    link: str
    keywords: tuple[str, ...]


NORMATIVE_ITEMS: list[KnowledgeItem] = [
    KnowledgeItem(
        title="Закон Республики Казахстан «Об образовании»",
        description="Базовый профильный закон для педагогов, администрации и организаций образования.",
        link="https://adilet.zan.kz/rus/docs/Z070000319_",
        keywords=("закон", "образование", "рк", "право"),
    ),
    KnowledgeItem(
        title="Правила и условия проведения аттестации педагогов",
        description="Официальные правила аттестации и подтверждения квалификации педагогов в Казахстане.",
        link="https://www.adilet.zan.kz/rus/docs/V1600013317",
        keywords=("аттестация", "педагог", "квалификация", "категория"),
    ),
    KnowledgeItem(
        title="Локальные акты организации образования",
        description="Подборка и шаблоны локальных актов школы: положения, регламенты и внутренние правила.",
        link="https://uba.edu.kz/ru/methodology/2",
        keywords=("локальные акты", "локальный акт", "положение", "регламент", "внутренние правила"),
    ),
    KnowledgeItem(
        title="ГОСО по уровням образования",
        description="Государственные общеобязательные стандарты дошкольного, среднего и профессионального образования.",
        link="https://www.adilet.zan.kz/rus/docs/V2200029031",
        keywords=("госо", "стандарт", "программа", "требования"),
    ),
    KnowledgeItem(
        title="Санитарные требования к объектам воспитания и образования",
        description="Санитарно-эпидемиологические требования к условиям обучения, питанию и режиму.",
        link="https://www.adilet.zan.kz/rus/docs/P1100001684",
        keywords=("санитарные правила", "санитария", "расписание", "нагрузка"),
    ),
    KnowledgeItem(
        title="Типовые учебные планы РК",
        description="Типовые учебные планы начального, основного среднего и общего среднего образования.",
        link="https://www.adilet.zan.kz/rus/docs/V1200008170",
        keywords=("типовой учебный план", "туп", "учебный план", "нагрузка"),
    ),
]

METHODICAL_ITEMS: list[KnowledgeItem] = [
    KnowledgeItem(
        title="Ведение электронного журнала",
        description="Практические рекомендации по корректному ведению электронного журнала и выставлению оценок.",
        link="https://kundelik.kz/",
        keywords=("kundelik", "журнал", "электронный журнал", "оценки", "заполнение"),
    ),
    KnowledgeItem(
        title="Шаблон рабочей программы",
        description="Структура рабочей программы по ГОСО и типовым учебным планам Казахстана.",
        link="https://www.adilet.zan.kz/rus/docs/V2200029031",
        keywords=("рабочая программа", "шаблон", "программа"),
    ),
    KnowledgeItem(
        title="Конструктор урока",
        description="Подсказки по структуре современного урока с учетом целей обучения и критериев оценивания.",
        link="https://uba.edu.kz/ru",
        keywords=("урок", "конструктор", "план", "цель"),
    ),
    KnowledgeItem(
        title="Повышение квалификации и методическая отчетность",
        description="Материалы по планированию методической работы, отчетности и повышению квалификации педагога.",
        link="https://www.adilet.zan.kz/rus/docs/V2000020361",
        keywords=("отчет", "отчетность", "повышение квалификации", "форма"),
    ),
]

METHODICAL_FAQ: list[tuple[str, str]] = [
    (
        "Как оформить рабочую программу?",
        "Опирайтесь на ГОСО и типовой учебный план, добавьте цели обучения, критерии оценивания и тематическое планирование.",
    ),
    (
        "Что делать, если не удается закрыть журнал вовремя?",
        "Проверьте пропуски, комментарии к оценкам и обратитесь к школьному администратору Kundelik при технической ошибке.",
    ),
    (
        "Как подготовить отчет по итогам четверти в школе Казахстана?",
        "Соберите данные по успеваемости, посещаемости, СОР/СОЧ и кратко зафиксируйте выводы и корректирующие действия.",
    ),
]


CATEGORY_TITLES = {
    "normative": "Нормативы",
    "methodical_help": "Методическая помощь",
    "event_formats": "Форматы мероприятий",
    "methodical_activity": "Методическая деятельность",
}


QUESTION_TAGS = {
    "normative": TAG_NORMATIVE,
    "methodical_help": TAG_METHOD_HELP,
}


SUGGESTION_TAGS = {
    "event_formats": TAG_EVENT,
    "methodical_activity": TAG_METHOD_IDEA,
}


def search_items(category: str, query: str) -> list[KnowledgeItem]:
    normalized = query.casefold().strip()
    if not normalized:
        return []

    items: Iterable[KnowledgeItem]
    if category == "normative":
        items = NORMATIVE_ITEMS
    elif category == "methodical_help":
        items = METHODICAL_ITEMS
    else:
        return []

    return [
        item
        for item in items
        if normalized in item.title.casefold()
        or normalized in item.description.casefold()
        or any(normalized in keyword.casefold() for keyword in item.keywords)
    ]


def get_category_items(category: str) -> list[KnowledgeItem]:
    if category == "normative":
        return NORMATIVE_ITEMS
    if category == "methodical_help":
        return METHODICAL_ITEMS
    return []


def get_methodical_faq() -> list[tuple[str, str]]:
    return METHODICAL_FAQ


def replace_category_items(category: str, items: list[KnowledgeItem]) -> None:
    target = get_category_items(category)
    target.clear()
    target.extend(items)


def replace_methodical_faq(items: list[tuple[str, str]]) -> None:
    METHODICAL_FAQ.clear()
    METHODICAL_FAQ.extend(items)


def get_section_stats() -> dict[str, int]:
    return {
        "normative_count": len(NORMATIVE_ITEMS),
        "methodical_count": len(METHODICAL_ITEMS),
        "faq_count": len(METHODICAL_FAQ),
    }


def search_all_items(query: str) -> list[tuple[str, KnowledgeItem]]:
    results: list[tuple[str, KnowledgeItem]] = []
    for category in ("normative", "methodical_help"):
        for item in search_items(category, query):
            results.append((category, item))
    return results
