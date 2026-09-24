"""Seguridad: hash y verificación de contraseñas con bcrypt.

Por qué bcrypt y no SHA/MD5:
- bcrypt es lento a propósito (resistente a ataques de fuerza bruta).
- genera un "salt" aleatorio: dos contraseñas iguales producen hashes distintos.
- es un hash unidireccional: NO se puede recuperar la contraseña original.
"""

import bcrypt


def hash_password(password: str) -> str:
    """Devuelve el hash de la contraseña listo para guardar en la BD."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Compara una contraseña en claro contra el hash guardado."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
