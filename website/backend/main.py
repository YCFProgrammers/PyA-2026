from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers import challenge_controller
from database.db import init_db
from database.tablondb import init_tablon_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()
    await init_tablon_db()

app.include_router(challenge_controller.router, prefix="/api")