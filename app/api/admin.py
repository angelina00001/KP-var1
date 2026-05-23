from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi.responses import HTMLResponse
from typing import Optional
from app.database import get_db
from app.models import User, Device
from app.services.auth_service import AuthService

router = APIRouter()


# ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ==========


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    """Удалить пользователя (только для админов)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Не авторизован")

    token = auth_header[7:]
    payload = AuthService.decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Неверный токен")

    current_user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == current_user_id))
    current_user = result.scalar_one_or_none()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Требуются права администратора")

    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    await db.delete(user)
    await db.commit()

    return {"message": f"Пользователь {user.email} удалён"}


@router.put("/users/{user_id}/disable-2fa")
async def admin_disable_2fa(
    user_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    """Только ВЫКЛЮЧИТЬ 2FA пользователю (принудительно сбросить)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Не авторизован")

    token = auth_header[7:]
    payload = AuthService.decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Неверный токен")

    current_user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == current_user_id))
    current_user = result.scalar_one_or_none()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Требуются права администратора")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Принудительно выключаем 2FA
    user.tfa_enabled = False
    await db.commit()

    return {"message": f"2FA для {user.email} принудительно ВЫКЛЮЧЕНА"}


@router.put("/users/{user_id}/toggle-admin")
async def admin_toggle_admin(
    user_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    """Назначить/снять права администратора"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Не авторизован")

    token = auth_header[7:]
    payload = AuthService.decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Неверный токен")

    current_user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == current_user_id))
    current_user = result.scalar_one_or_none()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Требуются права администратора")

    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Нельзя изменить права самого себя")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.is_admin = not user.is_admin
    await db.commit()

    role = "администратором" if user.is_admin else "обычным пользователем"
    return {
        "message": f"Пользователь {user.email} назначен {role}",
        "is_admin": user.is_admin,
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, token: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    # Получаем текущего пользователя
    current_user = None

    if token:
        payload = AuthService.decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = int(payload.get("sub"))
            result = await db.execute(select(User).where(User.id == user_id))
            current_user = result.scalar_one_or_none()

    if not current_user:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = AuthService.decode_token(token)
            if payload and payload.get("type") == "access":
                user_id = int(payload.get("sub"))
                result = await db.execute(select(User).where(User.id == user_id))
                current_user = result.scalar_one_or_none()

    if not current_user:
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head><title>Доступ запрещён</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>⛔ Не авторизован</h1>
            <p>Пожалуйста, <a href="/">войдите в аккаунт</a></p>
        </body>
        </html>
        """,
            status_code=401,
        )

    if not current_user.is_admin:
        return HTMLResponse(
            content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Доступ запрещён</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>⛔ Доступ запрещён</h1>
            <p>Вы вошли как <strong>{current_user.email}</strong>, но у вас нет прав администратора.</p>
            <p><a href="/">Вернуться на главную</a></p>
        </body>
        </html>
        """,
            status_code=403,
        )

    # Статистика
    total_users = (
        await db.execute(select(func.count()).select_from(User))
    ).scalar() or 0
    tfa_users = (
        await db.execute(
            select(func.count()).select_from(User).where(User.tfa_enabled == True)
        )
    ).scalar() or 0
    total_devices = (
        await db.execute(select(func.count()).select_from(Device))
    ).scalar() or 0

    # Список пользователей с их устройствами
    users_result = await db.execute(select(User))
    users = users_result.scalars().all()

    rows = ""
    for u in users:
        # Получаем устройства пользователя
        devices_result = await db.execute(select(Device).where(Device.user_id == u.id))
        devices = devices_result.scalars().all()
        devices_text = ""
        for d in devices:
            devices_text += f"📱 {d.device_name}<br>"
        if not devices_text:
            devices_text = "—"

        rows += f"""
        <tr>
            <td>{u.id}</td>
            <td>{u.email}</td>
            <td>{u.full_name}</td>
            <td style="text-align: center;">{'✅' if u.tfa_enabled else '❌'}</td>
            <td style="text-align: center;">{'👑' if u.is_admin else '👤'}</td>
            <td style="font-size: 12px;">{devices_text}</td>
            <td style="white-space: nowrap;">
                {f'<button onclick="disable2FA({u.id})" style="background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 10px; cursor: pointer; margin: 2px;">🔐 Выкл 2FA</button>' if u.tfa_enabled else '<span style="color: #999;">2FA выкл</span>'}
                <button onclick="toggleAdmin({u.id}, {str(u.is_admin).lower()})" style="background: #d4619b; color: white; border: none; padding: 5px 10px; border-radius: 10px; cursor: pointer; margin: 2px;">
                    {'👑 Снять админа' if u.is_admin else '👤 Сделать админом'}
                </button>
                {'<button onclick="deleteUser(' + str(u.id) + ')" style="background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 10px; cursor: pointer; margin: 2px;">🗑️ Удалить</button>' if u.id != current_user.id else '<span style="color: #999;">(Вы)</span>'}
            </td>
        </tr>
        """

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='UTF-8'>
        <title>Админ-панель</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #fff5f8; padding: 20px; }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            .card {{ background: white; border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); }}
            h1 {{ color: #d4619b; }}
            .stats {{ display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }}
            .stat {{ background: linear-gradient(135deg, #ffb6d9, #ff9ec7); color: white; padding: 20px; border-radius: 15px; flex: 1; min-width: 150px; text-align: center; }}
            .stat h3 {{ margin: 0; font-size: 14px; opacity: 0.9; }}
            .stat .number {{ font-size: 32px; font-weight: bold; margin: 10px 0 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background: #ffe0ec; color: #d4619b; }}
            .btn {{ display: inline-block; background: #d4619b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 25px; margin-top: 15px; }}
            .btn:hover {{ background: #b8407a; }}
            .message {{ position: fixed; top: 20px; right: 20px; background: #4CAF50; color: white; padding: 15px; border-radius: 10px; z-index: 1000; }}
            .message-error {{ background: #e74c3c; }}
        </style>
        <script>
            function showMessage(msg, isError = false) {{
                let div = document.createElement('div');
                div.className = 'message' + (isError ? ' message-error' : '');
                div.innerHTML = msg;
                document.body.appendChild(div);
                setTimeout(() => div.remove(), 3000);
            }}
            
            async function disable2FA(userId) {{
                if (!confirm('Вы уверены, что хотите принудительно ВЫКЛЮЧИТЬ 2FA этому пользователю?')) return;
                try {{
                    let token = localStorage.getItem('access_token');
                    let res = await fetch(`/api/v1/admin/users/${{userId}}/disable-2fa`, {{
                        method: 'PUT',
                        headers: {{ 'Authorization': `Bearer ${{token}}` }}
                    }});
                    let data = await res.json();
                    if (res.ok) {{
                        showMessage(data.message);
                        setTimeout(() => location.reload(), 1000);
                    }} else {{
                        showMessage(data.detail || 'Ошибка', true);
                    }}
                }} catch(e) {{
                    showMessage('Ошибка: ' + e.message, true);
                }}
            }}
            
            async function toggleAdmin(userId, currentState) {{
                let action = currentState ? 'снять права администратора' : 'назначить администратором';
                if (!confirm(`Вы уверены, что хотите ${{action}} этого пользователя?`)) return;
                try {{
                    let token = localStorage.getItem('access_token');
                    let res = await fetch(`/api/v1/admin/users/${{userId}}/toggle-admin`, {{
                        method: 'PUT',
                        headers: {{ 'Authorization': `Bearer ${{token}}` }}
                    }});
                    let data = await res.json();
                    if (res.ok) {{
                        showMessage(data.message);
                        setTimeout(() => location.reload(), 1000);
                    }} else {{
                        showMessage(data.detail || 'Ошибка', true);
                    }}
                }} catch(e) {{
                    showMessage('Ошибка: ' + e.message, true);
                }}
            }}
            
            async function deleteUser(userId) {{
                if (!confirm('ВНИМАНИЕ! Вы уверены, что хотите УДАЛИТЬ этого пользователя? Это действие необратимо.')) return;
                try {{
                    let token = localStorage.getItem('access_token');
                    let res = await fetch(`/api/v1/admin/users/${{userId}}`, {{
                        method: 'DELETE',
                        headers: {{ 'Authorization': `Bearer ${{token}}` }}
                    }});
                    let data = await res.json();
                    if (res.ok) {{
                        showMessage(data.message);
                        setTimeout(() => location.reload(), 1000);
                    }} else {{
                        showMessage(data.detail || 'Ошибка', true);
                    }}
                }} catch(e) {{
                    showMessage('Ошибка: ' + e.message, true);
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>🌸 Админ-панель</h1>
                <p>Добро пожаловать, {current_user.email}!</p>
            </div>
            
            <div class="stats">
                <div class="stat"><h3>👥 Пользователей</h3><div class="number">{total_users}</div></div>
                <div class="stat"><h3>🔐 2FA включена</h3><div class="number">{tfa_users}</div></div>
                <div class="stat"><h3>📱 Устройств</h3><div class="number">{total_devices}</div></div>
            </div>
            
            <div class="card">
                <h2>📋 Управление пользователями</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Email</th>
                                <th>Имя</th>
                                <th style="text-align:center">2FA</th>
                                <th style="text-align:center">Роль</th>
                                <th>Устройства</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows}
                        </tbody>
                    </table>
                </div>
                <a href="/" class="btn">🔙 На главную</a>
            </div>
        </div>
    </body>
    </html>
    """)
