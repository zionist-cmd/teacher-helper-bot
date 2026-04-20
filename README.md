# Помощник Педагога

Асинхронный Telegram-бот на `aiogram` 3 для педагогов, методистов и администрации организаций образования Казахстана.

## Что уже реализовано

- регистрация пользователя при первом входе: ФИО и номер школы;
- главное меню из четырех разделов по ТЗ;
- разделы "Нормативы" и "Методическая помощь" с поиском по ключевым словам;
- FAQ и подборка материалов;
- отправка пользовательских вопросов модератору;
- сбор предложений по форматам мероприятий и методической деятельности;
- автоматическая маркировка обращений тегами;
- локализация базы знаний и подсказок под нормативную и методическую практику Казахстана;
- поддержка внешней базы знаний из Google Sheets CSV с fallback на встроенный контент;
- сохранение данных в SQLite;
- опциональный demo-режим с историческими обращениями и виртуальной датой запуска;
- раздельные чаты для вопросов и предложений с fail-fast проверкой на старте;
- выгрузка обращений в Excel командой `/export` и фоновой недельной отправкой.

## Структура

```text
.
├── app
│   ├── config.py
│   ├── db.py
│   ├── handlers.py
│   ├── keyboards.py
│   ├── knowledge_base.py
│   ├── states.py
│   └── services
│       ├── content_loader.py
│       ├── exporter.py
│       ├── history_seed.py
│       └── weekly_export.py
├── .env.example
├── main.py
└── requirements.txt
```

## Запуск

1. Создайте виртуальное окружение:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Установите зависимости:

```powershell
pip install -r requirements.txt
```

3. Создайте `.env` на основе примера для локального запуска:

```env
BOT_TOKEN=
ADMIN_CHAT_ID=
QUESTIONS_CHAT_ID=
SUGGESTIONS_CHAT_ID=
DB_PATH=bot.sqlite3
EXPORT_DIR=exports
DEMO_MODE=false
VIRTUAL_LAUNCH_DATE=2025-09-01
BOT_TIMEZONE=Asia/Qyzylorda
WEEKLY_EXPORT_ENABLED=false
WEEKLY_EXPORT_WEEKDAY=0
WEEKLY_EXPORT_HOUR=9
WEEKLY_EXPORT_MINUTE=0
STARTUP_DELAY_SECONDS=0
NORMATIVE_SHEET_CSV_URL=
METHODICAL_SHEET_CSV_URL=
FAQ_SHEET_CSV_URL=
```

4. Запустите бота:

```powershell
python main.py
```

Для Amvera и любого другого хостинга не храните боевой `.env` в проекте.
Секреты нужно задавать через переменные окружения в панели хостинга.

## Развертывание в Amvera

В проект уже добавлен файл [amvera.yml](/C:/Users/АЛмас/Desktop/Телегабот/amvera.yml), настроенный под `Python Pip` и постоянное хранилище `/data`.

Что важно для этого проекта в Amvera:

- база SQLite и Excel-выгрузки должны лежать в `/data`, а не в репозитории;
- при запуске в Amvera бот сам использует безопасные дефолты `DB_PATH=/data/bot.sqlite3`, `EXPORT_DIR=/data/exports` и `STARTUP_DELAY_SECONDS=5`;
- токен и chat id задаются только через раздел «Переменные / Секреты»;
- для нормальных логов добавьте переменную `PYTHONUNBUFFERED=1`.

Минимальный набор секретов/переменных для панели Amvera:

```env
BOT_TOKEN=...
ADMIN_CHAT_ID=...
QUESTIONS_CHAT_ID=...
SUGGESTIONS_CHAT_ID=...
PYTHONUNBUFFERED=1
```

Опционально можно задать:

```env
DB_PATH=/data/bot.sqlite3
EXPORT_DIR=/data/exports
STARTUP_DELAY_SECONDS=5
WEEKLY_EXPORT_ENABLED=true
WEEKLY_EXPORT_WEEKDAY=0
WEEKLY_EXPORT_HOUR=9
WEEKLY_EXPORT_MINUTE=0
BOT_TIMEZONE=Asia/Qyzylorda
```

Порядок деплоя:

1. Создайте приложение в Amvera с окружением `Python Pip`.
2. Подключите репозиторий или загрузите код с файлом `amvera.yml` в корне.
3. В разделе переменных добавьте секреты и chat id.
4. Убедитесь, что бот добавлен в админский чат и модераторские чаты.
5. Запустите сборку и проверьте лог приложения.

## Команды

- `/start` — старт и регистрация пользователя;
- `/menu` — показать главное меню;
- `/search отпуск` — общий поиск по базе знаний;
- `/export` — выгрузка всех предложений в `.xlsx` для администратора;
- `/export_weekly` — выгрузка предложений за последние 7 дней.

## Google Sheets

Для внешнего контента используйте только опубликованные CSV-ссылки Google Sheets:

- `NORMATIVE_SHEET_CSV_URL` — колонки `title`, `description`, `link`, `keywords`
- `METHODICAL_SHEET_CSV_URL` — колонки `title`, `description`, `link`, `keywords`
- `FAQ_SHEET_CSV_URL` — колонки `question`, `answer`

Если ссылки не заданы, бот использует встроенную базу знаний.

## Что важно до продакшена

- `DEMO_MODE=true` включайте только для демонстрационного стенда, а не для рабочего контура;
- при необходимости скорректировать `VIRTUAL_LAUNCH_DATE`, если нужна другая дата имитации запуска;
- для фоновой недельной выгрузки включите `WEEKLY_EXPORT_ENABLED=true` и задайте время отправки;
- `QUESTIONS_CHAT_ID` и `SUGGESTIONS_CHAT_ID` можно развести по разным модераторским чатам;
- бот на старте проверяет доступность `ADMIN_CHAT_ID`, `QUESTIONS_CHAT_ID` и `SUGGESTIONS_CHAT_ID`, поэтому placeholders и битые id больше не проходят;
- верхнее меню теперь работает на inline-навигации и не раздувает чат при переходах между разделами.
"# baljan" 
"# baljan" 
"# baljan" 
"# final_baljans_bot" 
"# i_wish_it-s_final_baljan" 
"# teacher-helper-bot" 
