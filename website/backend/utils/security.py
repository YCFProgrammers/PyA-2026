import bcrypt

def hash_password(password: str) -> str:
    # Convertimos el hash de bytes a string para guardarlo fácil en SQLite
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_str: str) -> bool:
    # Convertimos el string de la DB de vuelta a bytes para comparar
    return bcrypt.checkpw(password.encode('utf-8'), hashed_str.encode('utf-8'))