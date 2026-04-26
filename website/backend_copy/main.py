import sys
import os
from pathlib import Path

# --- ESTO ES LO MÁS IMPORTANTE ---
# Obtenemos la ruta absoluta de la carpeta 'backend'
backend_dir = Path(__file__).resolve().parent
# La insertamos en la posición 0 para que tenga prioridad total
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ahora las importaciones se hacen relativas a 'backend'
try:
    from database.db import init_db
    from database.tablondb import init_tablon_db, add_challenge, get_all_challenges
    from models.project_model import Project
except ImportError as e:
    print(f"❌ Error crítico de importación: {e}")
    # Esto te dirá dónde está buscando Python realmente
    print(f"Buscando en: {sys.path[0]}")
    sys.exit(1)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()
    await init_tablon_db()
    print("🚀 Sistema PyA iniciado correctamente.")

@app.get("/api/challenges")
async def list_challenges():
    return await get_all_challenges()

@app.post("/api/challenges")
async def create_challenge(data: Project, email: str = None):
    if not email:
        raise HTTPException(status_code=400, detail="Falta email")
    await add_challenge(email, data.title, data.description)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)