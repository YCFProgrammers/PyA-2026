import aiosqlite
import os
from pathlib import Path
from dotenv import load_dotenv
from utils import security
from datetime import datetime

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "config" / ".env"

load_dotenv(dotenv_path=ENV_PATH)
DB_PATH = os.getenv('DB_PATH')

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_ad TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def register(name: str, email: str, password: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        try:
            hashed_pw = security.hash_password(password)
            await conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)", 
                (name, email, hashed_pw)
            )
            await conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return None
        except Exception as e:
            print(f"Error inesperado en registro: {e}")
            return None

async def login(email: str, password: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        try:
            async with conn.execute("SELECT password FROM users WHERE email = ?", (email,)) as cursor:
                row = await cursor.fetchone() # Await necesario aquí
                if row:
                    # row[0] es la contraseña hasheada almacenada
                    return security.verify_password(password, row[0])
                return False
        except Exception as e:
            print(f"Error inesperado en login: {e}")
            return None

