from database.tablondb import add_challenge, get_all_challenges

async def create_challenge(email, data):
    # lógica (validaciones, reglas, etc.)
    await add_challenge(email, data.title, data.description)
    return {"status": "success"}

async def get_challenges():
    return await get_all_challenges()