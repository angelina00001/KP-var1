# Архитектура 2FA Service

## Контекст системы

```mermaid
flowchart LR
    Client[Веб-клиент / API-клиент]
    API[FastAPI 2FA Service]
    PG[(PostgreSQL)]
    RD[(Redis)]
    FCM[Firebase FCM]
    Mobile[Мобильное приложение]

    Client --> API
    API --> PG
    API --> RD
    API --> FCM
    FCM --> Mobile
    Mobile --> API
```

## Компоненты backend

```mermaid
flowchart TB
    subgraph API["app/api"]
        auth[auth]
        tfa[tfa]
        devices[devices]
        admin[admin]
        web[web]
    end

    subgraph Services["app/services"]
        AuthS[AuthService]
        TOTPS[TOTPService]
        PushS[PushService]
        Sess[totp_session]
    end

    API --> Services
    Services --> PG[(PostgreSQL)]
    Sess --> RD[(Redis)]
    PushS --> FCM[FCM]
```

## Сценарий TOTP (RFC 6238)

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant API as 2FA API
    participant R as Redis
    participant DB as PostgreSQL

    U->>API: POST /enable-totp
    API->>R: SET totp_setup (secret, TTL 10m)
    API-->>U: QR + secret

    U->>API: POST /verify-totp + код
    API->>R: GET/DEL totp_setup
    API->>DB: Device + backup codes (hash)
    API-->>U: backup_codes (plain, один раз)
```

## Слои данных

| Сущность | Таблица | Назначение |
|----------|---------|------------|
| User | users | Учётная запись, флаг tfa_enabled |
| Device | devices | TOTP / push устройства |
| BackupCode | backup_codes | Резервные коды (хеш Argon2) |

## Безопасность

- Пароли и резервные коды: **Argon2** (passlib).
- JWT: access / refresh / временный токен для шага 2FA.
- SAST: **Bandit** (код), **Safety** (зависимости) — см. `scripts/run_tests.sh` и CI.

## API-документация

Интерактивная спецификация после запуска сервиса:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
