# 2FA Service — двухфакторная аутентификация

**Курсовой проект (вариант 1)**  
**ФИО:** Авдошина Ангелина Евгеньевна  
**Группа:** 221331  
**Тема:** Система двухфакторной аутентификации (2FA) с поддержкой TOTP и push-уведомлений  
**Предметная область:** Аутентификация и управление доступом  
**Стек:** Python, FastAPI, PostgreSQL, Redis, Firebase Cloud Messaging  

[![CI/CD Pipeline](https://github.com/angelina00001/KP-var1/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/angelina00001/KP-var1/actions/workflows/ci-cd.yml)

---

## О проекте

Микросервис 2FA для веб-приложений:

- **TOTP** (RFC 6238) — Google Authenticator, QR-код, резервные коды
- **Push** — подтверждение входа через FCM (мобильный клиент — в разработке)
- **REST API** для интеграции (`/api/v1/...`)
- **Веб-интерфейс** и **админ-панель**

---

## Какая версия Python нужна?

| Где | Версия |
|-----|--------|
| **Официально для проекта** | **Python 3.12** (Docker, GitHub Actions, файл `.python-version`) |
| У вас сейчас | Python 3.14.3 — **можно запускать**, но не рекомендуется для сдачи |

**Переделывать весь проект под 3.12 не нужно** — код обычный Python 3.12+ без специфики 3.14. Уже настроено:

- образ Docker: `python:3.12-slim`;
- CI: `PYTHON_VERSION: "3.12"`.

**Почему лучше поставить 3.12 на ПК:** у части библиотек (раньше `pillow==10.1.0`, старый `safety`) нет стабильных сборок под 3.14; на 3.12 установка `pip install -r requirements-dev.txt` проходит предсказуемо, как у проверяющего.

**Скачать Python 3.12:** https://www.python.org/downloads/release/python-31212/  
При установке отметьте **«Add python.exe to PATH»**.

Проверка:

```powershell
py -3.12 --version
```

Рекомендуемое виртуальное окружение:

```powershell
cd C:\Users\Ангелина\Downloads\2fa_service
py -3.12 -m venv venv
.\venv\Scripts\activate
python --version
```

Должно быть `Python 3.12.x`. Дальше все команды `pip` и `pytest` — **внутри активированного venv**.

---

## Что установить на компьютер (с нуля)

| № | Программа | Зачем | Ссылка |
|---|-----------|--------|--------|
| 1 | **Git** | Клонировать репозиторий | https://git-scm.com/download/win |
| 2 | **Python 3.12** | Запуск сервера и тестов | https://www.python.org/downloads/ |
| 3 | **Docker Desktop** | PostgreSQL и Redis в контейнерах | https://www.docker.com/products/docker-desktop/ |
| 4 | **Редактор** (по желанию) | VS Code / Cursor | https://code.visualstudio.com/ |

Отдельно ставить PostgreSQL или Redis на Windows **не обязательно** — их поднимает Docker.

Библиотеки Python (`fastapi`, `pytest` и т.д.) ставятся **одной командой** из файлов `requirements.txt` и `requirements-dev.txt` (см. ниже).

---

## Пошаговый запуск (Windows, с нуля)

### Шаг 0. Открыть командную строку

`Win + R` → `powershell` → Enter.

Перейти в папку проекта (путь замените на свой):

```powershell
cd C:\Users\Ангелина\Downloads\2fa_service
```

### Шаг 1. Скачать проект

Если уже есть папка — пропустите.

```powershell
git clone https://github.com/angelina00001/KP-var1.git
cd KP-var1
```

### Шаг 2. Виртуальное окружение и библиотеки

```powershell
py -3.12 -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
```

Если Python 3.12 нет, только 3.14:

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install "pillow>=11.0.0"
pip install -r requirements-dev.txt
```

Ошибки Windows/Docker: [docs/LOCAL_SETUP_WINDOWS.md](docs/LOCAL_SETUP_WINDOWS.md).

### Шаг 3. Файл настроек `.env`

```powershell
copy .env.example .env
```

В `.env` минимум смените `SECRET_KEY` на любую длинную случайную строку.  
Для локального запуска без Firebase можно оставить пути из примера; push позже потребует `firebase-credentials.json`.

### Шаг 4. Запустить Docker Desktop

1. Откройте **Docker Desktop**.
2. Дождитесь статуса **Running** (зелёный).
3. В PowerShell:

```powershell
docker compose up -d postgres redis
```

Проверка:

```powershell
docker compose ps
```

Должны быть `postgres` и `redis` в состоянии `running`.

### Шаг 5. Запустить API-сервер

```powershell
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Окно **не закрывайте** — сервер работает, пока оно открыто.

### Шаг 6. Открыть в браузере

| Что | Адрес |
|-----|--------|
| Главная страница (веб) | http://localhost:8000/ |
| Документация API (Swagger) | http://localhost:8000/docs |
| Альтернативная документация (ReDoc) | http://localhost:8000/redoc |
| Проверка «сервер жив» | http://localhost:8000/health |
| Adminer (просмотр БД) | http://localhost:8080/ (логин `postgres`, пароль `secret`, сервер `postgres`) |

Если страница не открывается — проверьте, что `uvicorn` запущен и порт 8000 не занят другой программой.

### Шаг 7. Запуск всего в Docker (альтернатива)

Без ручного `uvicorn` — всё в контейнерах:

```powershell
docker compose up -d
```

Те же ссылки: http://localhost:8000/docs и т.д.

---

## Тесты

**Без Docker** (только логика, 23 теста):

```powershell
.\venv\Scripts\activate
pytest tests/ -m "not integration"
```

**С Docker** (включая тесты с базой):

```powershell
docker compose up -d postgres redis
pytest tests/
```

**SAST** (безопасность кода и зависимостей):

```powershell
bandit -r app/
safety check
```

---

## Про httpx и «новый API» (для отчёта)

В тестах используется библиотека **httpx** — она имитирует HTTP-запросы к FastAPI без реального сетевого сервера.

**Раньше** (httpx до ~0.27):

```python
async with AsyncClient(app=app, base_url="http://test") as client:
    response = await client.get("/health")
```

**Сейчас** (httpx 0.27+) параметр `app=` убрали. Нужно явно указать транспорт ASGI:

```python
from httpx import ASGITransport, AsyncClient

async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
    response = await client.get("/health")
```

В репозитории в `requirements.txt` указано `httpx==0.25.1` (старый стиль тоже работает). Если `pip` поставил httpx 0.28+ (как при установке без venv на 3.14), старые тесты падали с `unexpected keyword argument 'app'`. В `tests/test_api.py` уже используется **новый вариант** — он совместим и со старым, и с новым httpx.

---

## Про `safety>=2.0`

В `requirements.txt` и `requirements-dev.txt` указано `safety>=2.0`, потому что старые версии Safety конфликтовали с окружением и падали при `safety check`. Это настройка **инструмента SAST**, не логики 2FA.

---

## Обязательные компоненты (курсовая)

| Компонент | Где в проекте |
|-----------|----------------|
| Git, семантические коммиты, Git Flow | [GITFLOW.md](GITFLOW.md) |
| Тестирование (pytest) | `tests/`, `pytest.ini` |
| Docker | `docker/Dockerfile`, `docker-compose.yml` |
| Документация | README, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), `/docs` |
| SAST | Bandit, Safety — CI и `scripts/run_tests.sh` |

---

## API (кратко)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/auth/signup` | Регистрация |
| POST | `/api/v1/auth/login` | Вход |
| POST | `/api/v1/tfa/enable-totp` | Начало настройки TOTP |
| POST | `/api/v1/tfa/verify-totp` | Подтверждение TOTP |
| POST | `/api/v1/tfa/verify` | Вход с кодом 2FA |
| GET | `/api/v1/devices/` | Список устройств |
| GET | `/health` | Health check |

---

## Структура репозитория

```
├── app/              # Код FastAPI
├── tests/            # Тесты pytest
├── docker/           # Dockerfile
├── docs/             # Архитектура, Windows
├── scripts/          # setup_dev.ps1, run_tests.sh
├── docker-compose.yml
├── requirements.txt
└── requirements-dev.txt
```

---

## GitHub

```powershell
git remote add origin https://github.com/angelina00001/KP-var1.git
git add .
git commit -m "feat: initial 2FA service for coursework"
git branch -M main
git push -u origin main
```

Подробнее о ветках: [GITFLOW.md](GITFLOW.md).

---

## Частые проблемы

| Симптом | Решение |
|---------|---------|
| `dockerDesktopLinuxEngine` не найден | Запустите **Docker Desktop** |
| `ModuleNotFoundError: httpx` / `pyotp` | `pip install -r requirements-dev.txt` в активированном `venv` |
| `pillow` не ставится | Python **3.12** или `pip install "pillow>=11.0.0"` |
| Порт 8000 занят | Закройте другой сервер или смените порт в команде `uvicorn` |

---

Учебный проект. Использование — в рамках курсовой работы.
