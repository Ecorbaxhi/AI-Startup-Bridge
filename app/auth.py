from pwdlib import PasswordHash
from starlette.requests import Request
from starlette.responses import RedirectResponse

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def current_user(request: Request):
    return request.session.get("user")


def require_role(request: Request, role: str):
    user = current_user(request)
    if not user or user["role"] != role:
        return None, RedirectResponse("/login", status_code=303)
    return user, None
