import aiosqlite
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH_TABLON = BASE_DIR / "database" / "tablon.db"

async def init_tablon_db():
    async with aiosqlite.connect(DB_PATH_TABLON) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_email TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_challenge(email: str, title: str, description: str):
    async with aiosqlite.connect(DB_PATH_TABLON) as db:
        await db.execute(
            "INSERT INTO challenges (author_email, title, description) VALUES (?, ?, ?)",
            (email, title, description)
        )
        await db.commit()

async def get_all_challenges():
    async with aiosqlite.connect(DB_PATH_TABLON) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM challenges ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]