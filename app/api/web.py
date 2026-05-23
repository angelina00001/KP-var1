from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def web_index(request: Request):
    html_path = Path(__file__).parent.parent.parent / "templates" / "index.html"

    if not html_path.exists():
        return HTMLResponse(
            content="<h1>Ошибка: файл index.html не найден</h1>", status_code=404
        )

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Здесь можно добавить динамические данные
    # html_content = html_content.replace("{{ title }}", "2FA Service")

    return HTMLResponse(content=html_content)
