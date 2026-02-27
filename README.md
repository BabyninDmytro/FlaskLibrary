# FlaskLibrary

**FlaskLibrary** — це вебзастосунок на Flask для публічної онлайн-бібліотеки з каталогом книжок, профілями читачів, відгуками та базовим REST API.

## Можливості
- Перегляд каталогу книжок на головній сторінці.
- Перегляд детальної сторінки книги.
- Реєстрація, вхід та профіль користувача.
- Додавання і перегляд відгуків.
- API-ендпоінти для роботи з бібліотекою (див. `openapi.yaml`).

## Технології
- Python 3
- Flask
- SQLAlchemy
- Flask-WTF
- Jinja2

## Структура проєкту
- `app/` — основна логіка застосунку (моделі, маршрути, сервіси, форми).
- `templates/` — HTML-шаблони.
- `tests/` — автотести.
- `openapi.yaml` — опис REST API.
- `run.py` — точка входу для запуску локально.

## Локальний запуск
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Після запуску відкрийте URL, який покаже Flask (зазвичай `http://127.0.0.1:5000`).

## Запуск тестів
```bash
pip install -r requirements-dev.txt
pytest
```

## API-документація
- OpenAPI-опис: `openapi.yaml`
- Додатковий опис і оцінка API: `REST_API_ASSESSMENT.md`
