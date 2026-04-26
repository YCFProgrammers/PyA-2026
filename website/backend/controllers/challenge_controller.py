from fastapi import APIRouter, HTTPException

from models.project_model import Project
from services.challenge_service import (
    create_challenge,
    get_challenges
)

router = APIRouter()

@router.get("/challenges")
async def list_challenges():
    return await get_challenges()

@router.post("/challenges")
async def create(data: Project, email: str = None):
    if not email:
        raise HTTPException(status_code=400, detail="Falta email")

    return await create_challenge(email, data)