# Git Flow и семантические коммиты

## Ветки (Git Flow)

| Ветка | Назначение |
|-------|------------|
| `main` | Стабильная версия, готовая к сдаче / демонстрации |
| `develop` | Интеграция новых возможностей |
| `feature/*` | Отдельные задачи (например `feature/totp-redis-session`) |
| `fix/*` | Исправления ошибок |
| `release/*` | Подготовка релиза перед merge в `main` |

### Типовой цикл

```bash
git checkout develop
git checkout -b feature/название-задачи
# ... коммиты ...
git checkout develop
git merge --no-ff feature/название-задачи
git branch -d feature/название-задачи
```

Релиз:

```bash
git checkout -b release/1.0.0 develop
git checkout main
git merge --no-ff release/1.0.0
git tag -a v1.0.0 -m "Релиз 1.0.0"
```

## Семантические коммиты (Conventional Commits)

Формат: `тип(область): краткое описание`

| Тип | Когда использовать |
|-----|-------------------|
| `feat` | Новая функциональность |
| `fix` | Исправление бага |
| `docs` | Только документация |
| `test` | Тесты |
| `refactor` | Рефакторинг без смены поведения |
| `chore` | Сборка, CI, зависимости |
| `ci` | Изменения GitHub Actions |
| `security` | Исправления безопасности, SAST |

Примеры:

```
feat(totp): хранение сессии настройки TOTP в Redis
fix(api): объединение маршрутов TOTP и push в одном router
docs(readme): данные автора курсовой работы
test(totp): проверка хеширования резервных кодов Argon2
ci: установка requirements-dev.txt в pipeline
```

## Репозиторий курсовой

- GitHub: https://github.com/angelina00001/KP-var1.git
- Основная ветка: `main`
