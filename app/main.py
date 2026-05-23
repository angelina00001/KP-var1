from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import admin, auth, devices, tfa, web
from app.config import settings
from app.database import Base, engine


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"{settings.app_name} started successfully")
    yield
    await engine.dispose()
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Сервис двухфакторной аутентификации (TOTP RFC 6238, push FCM). "
        "Курсовой проект, вариант 1. Авдошина Ангелина Евгеньевна, группа 221331."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(tfa.router, prefix="/api/v1/tfa", tags=["Two-Factor Authentication"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(web.router, tags=["Web"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}
