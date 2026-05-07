import logging
from pathlib import Path

import aiosqlite

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "warnings.db"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS warnings (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id  INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    mod_id    INTEGER NOT NULL,
    reason    TEXT,
    created   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_warn_user ON warnings(guild_id, user_id);
"""


async def init() -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.executescript(CREATE_SQL)
        await conn.commit()


async def add_warning(guild_id: int, user_id: int, mod_id: int, reason: str) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "INSERT INTO warnings (guild_id, user_id, mod_id, reason) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, mod_id, reason),
        )
        await conn.commit()
        # devolver número total de warnings del usuario en este guild
        async with conn.execute(
            "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ) as c:
            row = await c.fetchone()
            return int(row[0]) if row else 0


async def get_warnings(guild_id: int, user_id: int) -> list[tuple]:
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute(
            "SELECT id, mod_id, reason, created FROM warnings "
            "WHERE guild_id = ? AND user_id = ? ORDER BY id DESC",
            (guild_id, user_id),
        ) as cur:
            return await cur.fetchall()


async def clear_warnings(guild_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        await conn.commit()
        return cur.rowcount or 0
