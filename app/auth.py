import secrets

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


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def verify_csrf(request: Request, token: str) -> bool:
    expected = request.session.get("csrf_token")
    return bool(expected and token and secrets.compare_digest(expected, token))


def require_role(request: Request, role: str):
    user = current_user(request)
    if not user or user["role"] != role:
        return None, RedirectResponse("/login", status_code=303)
    return user, None
