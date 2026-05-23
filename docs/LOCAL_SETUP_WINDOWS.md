# Локальный запуск на Windows

Полная пошаговая инструкция с нуля — в **[README.md](../README.md)** (разделы «Что установить» и «Пошаговый запуск»).

## 1. Docker: ошибка `dockerDesktopLinuxEngine`

Сообщение означает, что **Docker Desktop не запущен** (или не установлен).

1. Установите [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
2. Запустите **Docker Desktop** и дождитесь статуса *Running*.
3. Повторите:

```powershell
docker compose up -d postgres redis
```

Без Docker можно запускать **только модульные тесты** (без PostgreSQL):

```powershell
pytest tests/ -m "not integration"
```

---

## 2. Тесты: `ModuleNotFoundError` (httpx, jose, pyotp…)

Зависимости **не установлены**. Один раз выполните:

```powershell
cd C:\Users\Ангелина\Downloads\2fa_service
powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
```

или вручную:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Если `pillow==10.1.0` не ставится на Python 3.14:

```powershell
python -m pip install "pillow>=11.0.0"
python -m pip install -r requirements-dev.txt
```

Рекомендуется для курсовой: **Python 3.12** (как в Docker и CI). Скачать: https://www.python.org/downloads/release/python-31212/

```powershell
py -3.12 -m venv venv
.\venv\Scripts\activate
pip install -r requirements-dev.txt
pytest tests/ -m "not integration"
```

---

## 3. Запуск тестов

```powershell
pytest tests/ -m "not integration"
```

С PostgreSQL и Redis (Docker должен работать):

```powershell
docker compose up -d postgres redis
pytest tests/
```
