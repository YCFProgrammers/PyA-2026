from database.db import create_user, get_user_by_email
from utils import security

async def register_user(name, email, password):
    hashed = security.hash_password(password)
    return await create_user(name, email, hashed)


async def login_user(email, password):
    user = await get_user_by_email(email)
    
    if not user:
        return None

    valid = security.verify_password(password, user[3])

    if not valid:
        return None

    return {
        "id": user[0],
        "name": user[1],
        "email": user[2]
    }