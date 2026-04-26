import os
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Correcto manejo de Google Auth
from google.oauth2 import id_token 
from google.auth.transport import requests
from dotenv import load_dotenv
from jose import jwt # pip install python-jose

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "config" / "log.env"
load_dotenv(dotenv_path=ENV_PATH)

app = FastAPI()

# Configuración JWT propia
SECRET_KEY = os.getenv("SECRET_KEY", "una_clave_muy_secreta_123")
ALGORITHM = "HS256"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CLIENT_ID = os.getenv('CLIENT_ID')

class TokenRequest(BaseModel):
    token: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


FRONTEND_DIR = BASE_DIR / "frontend"

@app.get("/")
async def read_root():
    return FileResponse(FRONTEND_DIR / "log.html")


@app.post("/auth/google") # Fíjate en el / antes de auth
async def auth_google(token_request: TokenRequest):
    try:
        id_info = id_token.verify_oauth2_token(
            token_request.token, 
            requests.Request(), 
            CLIENT_ID
        )

        # 2. Extraer info del usuario del token
        user_email = id_info.get('email')
        user_name = id_info.get('name')
        
        # 3. Generar sesión propia (JWT)
        access_token = create_access_token(data={"sub": user_email})

        return {
            "status": "success",
            "access_token": access_token,
            "user": {
                "email": user_email,
                "name": user_name,
                "picture": id_info.get('picture')
            }
        }
    except ValueError:
        # Error específico de token inválido
        raise HTTPException(status_code=400, detail="Token de Google inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


if __name__ == "__main__": 
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)