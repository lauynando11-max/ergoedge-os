"""
ERGOEDGE OS - Servidor Web FastAPI (Con Autenticación Simple)
"""

import os
import sys
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, Form, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

# Crear aplicación
app = FastAPI(title="ERGOEDGE OS")

# Configurar templates
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Crear carpetas estáticas
os.makedirs(str(BASE_DIR / "static/css"), exist_ok=True)
os.makedirs(str(BASE_DIR / "static/js"), exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ============ AUTENTICACIÓN SIMPLE ============
# Base de datos de usuarios (en memoria)
usuarios = {}


def hash_password(password: str) -> str:
    """Hashea una contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verificar_sesion(token: str = Cookie(None)) -> dict:
    """Verifica si el usuario tiene sesión activa"""
    if token and token in usuarios:
        return usuarios[token]
    return None


# ============ MIDDLEWARE PARA PASAR USUARIO A TODOS LOS TEMPLATES ============
@app.middleware("http")
async def add_user_to_context(request: Request, call_next):
    """Agrega el usuario logueado a request.state.usuario para todos los templates"""
    token = request.cookies.get("token")
    usuario = None
    if token and token in usuarios:
        usuario = usuarios[token]
    request.state.usuario = usuario
    response = await call_next(request)
    return response


# ============ RUTAS DE AUTENTICACIÓN ============

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    usuario = request.state.usuario
    # Si ya está logueado, redirigir al dashboard
    if usuario:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": error, "usuario": usuario})


@app.get("/registro", response_class=HTMLResponse)
async def registro_page(request: Request):
    usuario = request.state.usuario
    # Si ya está logueado, redirigir al dashboard
    if usuario:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("registro.html", {"request": request, "usuario": usuario})


@app.post("/registro")
async def registro(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    # Verificar si el email ya existe
    for user_data in usuarios.values():
        if user_data.get("email") == email:
            return templates.TemplateResponse("registro.html", {
                "request": request,
                "error": "Este correo ya está registrado",
                "usuario": None
            })
    
    # Crear nuevo usuario
    token = secrets.token_urlsafe(32)
    usuarios[token] = {
        "nombre": nombre,
        "email": email,
        "password": hash_password(password),
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }
    
    response = RedirectResponse(url="/login", status_code=303)
    return response


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    hashed = hash_password(password)
    
    # Buscar usuario
    for token, user_data in usuarios.items():
        if user_data["email"] == email and user_data["password"] == hashed:
            response = RedirectResponse(url="/dashboard", status_code=303)
            response.set_cookie(key="token", value=token, httponly=True)
            return response
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Correo o contraseña incorrectos",
        "usuario": None
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, token: str = Cookie(None)):
    usuario = verificar_sesion(token)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": usuario
    })


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("token")
    return response


# ============ TUS RUTAS EXISTENTES (actualizadas con usuario) ============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    usuario = request.state.usuario
    return templates.TemplateResponse("index.html", {"request": request, "usuario": usuario})


@app.get("/analisis", response_class=HTMLResponse)
async def analisis(request: Request):
    usuario = request.state.usuario
    return templates.TemplateResponse("analisis.html", {"request": request, "usuario": usuario})


@app.get("/rosa", response_class=HTMLResponse)
async def rosa_form(request: Request):
    usuario = request.state.usuario
    return templates.TemplateResponse("rosa_form.html", {"request": request, "usuario": usuario})


@app.post("/rosa/calcular", response_class=HTMLResponse)
async def rosa_calcular(
    request: Request,
    empresa: str = Form(...),
    puesto: str = Form(...),
    evaluador: str = Form(...),
    operario_nombre: str = Form(...),
    operario_edad: int = Form(...),
    operario_antiguedad: str = Form(...),
    operario_patologias: str = Form(""),
    uso_continuo: bool = Form(False)
):
    from Methods.metodologias.rosa import evaluar_rosa
    
    datos_rosa = {
        "silla": {"altura": 2, "apoyo_lumbar": "presente", "profundidad_asiento": "parcial", 
                  "apoyabrazos_altura": "ligero", "apoyabrazos_ancho": "parcial"},
        "monitor": {"altura": 2, "distancia": 60, "inclinacion": "perpendicular", "reflejos": False},
        "teclado": {"altura": "ligero", "distancia": 95, "inclinacion": "neutro", "reposamunecas": "basico"},
        "mouse": {"altura": "misma", "distancia": 5, "posicion": "frontal"},
        "uso_continuo": uso_continuo
    }
    
    resultado = evaluar_rosa(datos_rosa)
    usuario = request.state.usuario
    
    return templates.TemplateResponse("resultado_rosa.html", {
        "request": request,
        "resultado": resultado,
        "empresa": empresa,
        "operario": operario_nombre,
        "usuario": usuario
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)