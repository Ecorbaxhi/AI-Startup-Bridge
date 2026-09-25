import os
from getpass import getpass
from sqlalchemy import select
from app.auth import hash_password
from app.database import SessionLocal
from app.models import User

email = os.getenv('ADMIN_EMAIL') or input('Admin email: ').strip().lower()
password = os.getenv('ADMIN_PASSWORD') or getpass('Admin password: ')
if len(password) < 12: raise SystemExit('Use an admin password of at least 12 characters.')
db = SessionLocal()
user = db.scalar(select(User).where(User.email == email))
if user:
    user.password_hash = hash_password(password); user.role = 'admin'
else:
    db.add(User(email=email, password_hash=hash_password(password), role='admin'))
db.commit(); print(f'Admin account ready for {email}.')
