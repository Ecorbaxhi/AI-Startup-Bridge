# Albania AI Startup Bridge

A small, server-rendered talent and innovation pipeline connecting Albanian university students with technology startups. Startups publish real project needs; students create profiles, discover projects, apply, and receive transparent recommendations.

## Stack

Python 3.12, FastAPI, Uvicorn, Jinja2, SQLAlchemy 2, Alembic, PostgreSQL, signed session cookies, Argon2 password hashing, and pytest. Local development defaults to SQLite; production uses PostgreSQL through `DATABASE_URL`.

## Architecture

`app/main.py` owns the HTTP routes and server-rendered pages. `models.py` contains the relational data model. `matching.py` is a deterministic, explainable matcher with normalized skills and aliases. Templates and CSS are under `app/templates` and `app/static`. The optional OpenAI key is reserved for future explanations; the MVP does not require it.

## Local Windows setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. The local `.env` created for this workspace contains a generated session secret and is ignored by Git. Change the admin password before using admin provisioning in a real environment.

## Configuration

`DATABASE_URL`, `SESSION_SECRET_KEY`, `ENVIRONMENT`, and optional `OPENAI_API_KEY` are supported. `SESSION_SECRET_KEY` must be generated securely in production. Admin registration is deliberately not exposed in the public form; create an admin through a controlled server-side process. Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in a protected shell and run `python scripts/create_admin.py`; never put the password in Git.

## Tests and demo data

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\seed_demo.py
```

The seed script creates clearly fictional universities, students, startups, and projects. Its demo password is for local demonstration only and must never be used in production.

## GitHub and Render

Create a repository, then run `git remote add origin <your-repository-url>` and `git push -u origin main`. Do not commit `.env`, databases, credentials, or private user data.

`render.yaml` defines one Python web service and one managed PostgreSQL database. Render runs `alembic upgrade head` before Uvicorn, binds to the provided `PORT`, and generates `SESSION_SECRET_KEY`. Connect the repository in Render and review the generated environment variables before creating the service. The managed database and web service may require paid Render resources; plans and prices change, so check Render's current pricing. No deployment was performed from this workspace.

## Known limitations and next steps

This MVP uses basic signed sessions and form workflows. CSRF tokens, email verification, richer moderation/reporting, project editing/closing UI, and optional semantic explanations should be added before public launch. Add a production PostgreSQL test service and formal migration CI before handling real users.
