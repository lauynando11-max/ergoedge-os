"""
ERGOEDGE OS - Servidor Web (Versión Ultra Simple)
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from Methods.metodologias.rosa import evaluar_rosa

app = FastAPI(title="ERGOEDGE OS")


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ERGOEDGE OS</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .btn { background: #001f3f; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }
        </style>
    </head>
    <body>
        <h1>🧑‍💻 ERGOEDGE OS</h1>
        <p>Sistema de Análisis Ergonómico con IA</p>
        <a href="/rosa" class="btn">Evaluar ROSA</a>
    </body>
    </html>
    """


@app.get("/rosa", response_class=HTMLResponse)
async def rosa_form():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ROSA - Evaluación de Oficina</title>
        <style>
            body { font-family: Arial; padding: 20px; max-width: 600px; margin: auto; }
            input, select { width: 100%; padding: 8px; margin: 5px 0 15px 0; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #001f3f; color: white; padding: 10px; border: none; width: 100%; border-radius: 5px; cursor: pointer; }
            .card { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; }
            h2 { color: #001f3f; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>📋 ROSA - Evaluación de Oficina</h2>
            <form method="post" action="/rosa/calcular">
                <label>Empresa</label>
                <input type="text" name="empresa" required>
                
                <label>Puesto</label>
                <input type="text" name="puesto" required>
                
                <label>Operario</label>
                <input type="text" name="operario_nombre" required>
                
                <label>Edad</label>
                <input type="number" name="operario_edad" required>
                
                <label>Antigüedad</label>
                <input type="text" name="operario_antiguedad" required>
                
                <label>
                    <input type="checkbox" name="uso_continuo" value="true">
                    ¿Uso continuo >1 hora sin pausa?
                </label>
                
                <button type="submit">Evaluar Puesto</button>
            </form>
        </div>
    </body>
    </html>
    """


@app.post("/rosa/calcular", response_class=HTMLResponse)
async def rosa_calcular(
    empresa: str = Form(...),
    puesto: str = Form(...),
    operario_nombre: str = Form(...),
    operario_edad: int = Form(...),
    operario_antiguedad: str = Form(...),
    uso_continuo: bool = Form(False)
):
    # Datos de prueba para ROSA
    datos_rosa = {
        "silla": {"altura": 2, "apoyo_lumbar": "presente", "profundidad_asiento": "parcial", 
                  "apoyabrazos_altura": "ligero", "apoyabrazos_ancho": "parcial"},
        "monitor": {"altura": 2, "distancia": 60, "inclinacion": "perpendicular", "reflejos": False},
        "teclado": {"altura": "ligero", "distancia": 95, "inclinacion": "neutro", "reposamunecas": "basico"},
        "mouse": {"altura": "misma", "distancia": 5, "posicion": "frontal"},
        "uso_continuo": uso_continuo
    }
    
    resultado = evaluar_rosa(datos_rosa)
    
    # Determinar color según puntuación
    if resultado['puntuacion_final'] <= 4:
        color = "green"
    elif resultado['puntuacion_final'] <= 6:
        color = "orange"
    else:
        color = "red"
    
    recomendaciones_html = "".join(f'<li>{r}</li>' for r in resultado['recomendaciones'])
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resultados ROSA</title>
        <style>
            body {{ font-family: Arial; padding: 20px; max-width: 600px; margin: auto; background: #f5f5f5; }}
            .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .score {{ font-size: 48px; text-align: center; font-weight: bold; }}
            .green {{ color: #28a745; }}
            .yellow {{ color: #ffc107; }}
            .orange {{ color: #fd7e14; }}
            .red {{ color: #dc3545; }}
            h2 {{ color: #001f3f; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
            .btn {{ display: inline-block; margin-top: 20px; background: #001f3f; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>📊 Resultados ROSA</h2>
            <p><strong>Empresa:</strong> {empresa}</p>
            <p><strong>Puesto:</strong> {puesto}</p>
            <p><strong>Operario:</strong> {operario_nombre}</p>
            <p><strong>Edad:</strong> {operario_edad} años</p>
            <p><strong>Antigüedad:</strong> {operario_antiguedad}</p>
            
            <div class="score {color}">
                {resultado['puntuacion_final']}/10
            </div>
            
            <p style="text-align: center;"><strong>Nivel de Riesgo:</strong> {resultado['nivel_riesgo']}</p>
            <p style="text-align: center;"><strong>Acción:</strong> {resultado['accion']}</p>
            
            <h3>📊 Puntuaciones por componente:</h3>
            <table>
                <tr><td><strong>Silla</strong></td><td>{resultado['silla']}/10</td></tr>
                <tr><td><strong>Monitor</strong></td><td>{resultado['monitor']}/10</td></tr>
                <tr><td><strong>Teclado</strong></td><td>{resultado['teclado']}/10</td></tr>
                <tr><td><strong>Mouse</strong></td><td>{resultado['mouse']}/10</td></tr>
            </table>
            
            <h3>📋 Recomendaciones:</h3>
            <ul>
                {recomendaciones_html}
            </ul>
            
            <a href="/rosa" class="btn">← Nueva Evaluación</a>
            <a href="/" class="btn" style="background: #6c757d; margin-left: 10px;">🏠 Inicio</a>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    print("🚀 Servidor ERGOEDGE OS iniciado en http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)