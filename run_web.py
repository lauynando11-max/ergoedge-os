"""
ERGOEDGE OS - Servidor Web
Ejecutar con: python run_web.py
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 ERGOEDGE OS - Servidor Web")
    print("=" * 50)
    print("🌐 Abrir en navegador: http://127.0.0.1:8000")
    print("=" * 50)
    uvicorn.run("web_app.app:app", host="127.0.0.1", port=8000, reload=True)