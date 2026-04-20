from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.db import Database
from app.knowledge_base import TAG_EVENT, TAG_METHOD_HELP, TAG_METHOD_IDEA, TAG_NORMATIVE


@dataclass(frozen=True, slots=True)
class SeedRecord:
    full_name: str
    school: str
    category: str
    tag: str
    kind: str
    username: str
    telegram_id: int
    text: str
    offset_days: int


SEED_RECORDS: tuple[SeedRecord, ...] = (
    SeedRecord(
        full_name="Айжан Сериккызы",
        school="Школа-лицей №23",
        category="normative",
        tag=TAG_NORMATIVE,
        kind="question",
        username="aizhan_teacher",
        telegram_id=710001,
        text="Нужна ссылка на действующие правила аттестации педагогов для подготовки портфолио.",
        offset_days=4,
    ),
    SeedRecord(
        full_name="Руслан Бекмуханов",
        school="ОШ имени Абая",
        category="methodical_help",
        tag=TAG_METHOD_HELP,
        kind="question",
        username="ruslan_metod",
        telegram_id=710002,
        text="Подскажите шаблон краткосрочного плана урока по обновленному содержанию образования.",
        offset_days=16,
    ),
    SeedRecord(
        full_name="Гульмира Тажиева",
        school="Школа-гимназия №7",
        category="event_formats",
        tag=TAG_EVENT,
        kind="suggestion",
        username="gulmira_gym",
        telegram_id=710003,
        text="Предлагаю провести областной вебинар для классных руководителей по профилактике буллинга и работе с родителями.",
        offset_days=35,
    ),
    SeedRecord(
        full_name="Нуржан Омаров",
        school="Средняя школа №11",
        category="methodical_activity",
        tag=TAG_METHOD_IDEA,
        kind="suggestion",
        username="omarov_n",
        telegram_id=710004,
        text="Нужно обновить методические рекомендации по СОР и СОЧ, добавить типовые критерии оценивания по предметам.",
        offset_days=52,
    ),
    SeedRecord(
        full_name="Сауле Кайратовна",
        school="IT-лицей",
        category="normative",
        tag=TAG_NORMATIVE,
        kind="question",
        username="saule_it",
        telegram_id=710005,
        text="Где посмотреть действующие санитарные требования по учебной нагрузке и расписанию для школьников?",
        offset_days=79,
    ),
    SeedRecord(
        full_name="Данияр Есенов",
        school="Школа-гимназия №41",
        category="event_formats",
        tag=TAG_EVENT,
        kind="suggestion",
        username="daniyar_esen",
        telegram_id=710006,
        text="Прошу добавить формат очного мастер-класса по использованию ИИ-инструментов для подготовки уроков.",
        offset_days=101,
    ),
    SeedRecord(
        full_name="Асем Жумабекова",
        school="Средняя школа №5",
        category="methodical_help",
        tag=TAG_METHOD_HELP,
        kind="question",
        username="asem_zh",
        telegram_id=710007,
        text="Нужна памятка по заполнению электронного журнала Kundelik и фиксации домашних заданий.",
        offset_days=129,
    ),
    SeedRecord(
        full_name="Ерлан Тулеуов",
        school="Школа-лицей №2",
        category="methodical_activity",
        tag=TAG_METHOD_IDEA,
        kind="suggestion",
        username="yerlan_school",
        telegram_id=710008,
        text="Полезно сделать единый банк рабочих программ и краткосрочных планов для учителей района.",
        offset_days=148,
    ),
)


class HistorySeedService:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def ensure_seeded(self, launch_date: date) -> None:
        if await self.database.submissions_count():
            return

        for record in SEED_RECORDS:
            created_at = self._build_created_at(launch_date, record.offset_days)
            await self.database.upsert_user(
                telegram_id=record.telegram_id,
                username=record.username,
                full_name=record.full_name,
                school=record.school,
            )
            await self.database.create_submission(
                telegram_id=record.telegram_id,
                username=record.username,
                full_name=record.full_name,
                school=record.school,
                category=record.category,
                tag=record.tag,
                text=record.text,
                kind=record.kind,
                created_at=created_at,
            )

    def _build_created_at(self, launch_date: date, offset_days: int) -> str:
        value = datetime.combine(launch_date, datetime.min.time()) + timedelta(days=offset_days, hours=10)
        return value.strftime("%Y-%m-%d %H:%M:%S")
