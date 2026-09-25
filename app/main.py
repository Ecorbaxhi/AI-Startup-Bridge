from pathlib import Path
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.sessions import SessionMiddleware

from .auth import current_user, hash_password, require_role, verify_password
from .config import settings
from .database import Base, engine, get_db
from .matching import match_student_project
from .models import Application, Project, StartupProfile, StudentProfile, University, User

app = FastAPI(title="Albania AI Startup Bridge")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key, https_only=settings.environment == "production", same_site="lax")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


def render(request, name, **context):
    context["current"] = current_user(request)
    return templates.TemplateResponse(request=request, name=name, context=context)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    projects = db.scalars(select(Project).where(Project.status == "active").order_by(Project.created_at.desc()).limit(3)).all()
    return render(request, "index.html", projects=projects)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return render(request, "register.html")


@app.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    if role not in {"student", "startup"} or len(password) < 8:
        return render(request, "register.html", error="Choose a valid role and a password of at least 8 characters.")
    if db.scalar(select(User).where(User.email == email.lower().strip())):
        return render(request, "register.html", error="An account with that email already exists.")
    user = User(email=email.lower().strip(), password_hash=hash_password(password), role=role)
    db.add(user); db.commit(); db.refresh(user)
    request.session["user"] = {"id": user.id, "email": user.email, "role": user.role}
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render(request, "login.html")


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if not user or not verify_password(password, user.password_hash):
        return render(request, "login.html", error="Email or password is incorrect.")
    request.session["user"] = {"id": user.id, "email": user.email, "role": user.role}
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request)
    if not user: return RedirectResponse("/login", status_code=303)
    if user["role"] == "student": return RedirectResponse("/student/dashboard", status_code=303)
    if user["role"] == "startup": return RedirectResponse("/startup/dashboard", status_code=303)
    return RedirectResponse("/admin", status_code=303)


@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request, db: Session = Depends(get_db)):
    return render(request, "projects.html", projects=db.scalars(select(Project).where(Project.status == "active").order_by(Project.created_at.desc())).all())


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = db.scalar(select(Project).options(joinedload(Project.startup)).where(Project.id == project_id))
    if not project: return render(request, "error.html", message="Project not found.")
    return render(request, "project_detail.html", project=project)


@app.get("/student/dashboard", response_class=HTMLResponse)
def student_dashboard(request: Request, db: Session = Depends(get_db)):
    user, redirect = require_role(request, "student")
    if redirect: return redirect
    profile = db.scalar(select(StudentProfile).options(joinedload(StudentProfile.university)).where(StudentProfile.user_id == user["id"]))
    projects = db.scalars(select(Project).where(Project.status == "active")).all()
    recommendations = sorted([(project, match_student_project(profile, project)) for project in projects], key=lambda item: item[1]["score"], reverse=True) if profile else []
    applications = db.scalars(select(Application).options(joinedload(Application.project)).where(Application.student_id == profile.id)).all() if profile else []
    return render(request, "student_dashboard.html", profile=profile, recommendations=recommendations[:5], applications=applications)


@app.get("/student/profile", response_class=HTMLResponse)
def student_profile_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = require_role(request, "student")
    if redirect: return redirect
    return render(request, "student_profile.html", profile=db.scalar(select(StudentProfile).where(StudentProfile.user_id == user["id"])), universities=db.scalars(select(University).order_by(University.name)).all())


@app.post("/student/profile")
def student_profile(request: Request, full_name: str = Form(...), university_id: int | None = Form(None), field_of_study: str = Form(""), academic_year: str = Form(""), skills: str = Form(""), interests: str = Form(""), bio: str = Form(""), availability: str = Form(""), db: Session = Depends(get_db)):
    user, redirect = require_role(request, "student")
    if redirect: return redirect
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user["id"]))
    values = dict(full_name=full_name, university_id=university_id, field_of_study=field_of_study, academic_year=academic_year, skills=[x.strip() for x in skills.split(",") if x.strip()], interests=[x.strip() for x in interests.split(",") if x.strip()], bio=bio, availability=availability)
    if profile: [setattr(profile, key, value) for key, value in values.items()]
    else: db.add(StudentProfile(user_id=user["id"], **values))
    db.commit(); return RedirectResponse("/student/dashboard", status_code=303)


@app.post("/projects/{project_id}/apply")
def apply(request: Request, project_id: int, message: str = Form(...), db: Session = Depends(get_db)):
    user, redirect = require_role(request, "student")
    if redirect: return redirect
    student = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user["id"]))
    project = db.get(Project, project_id)
    if not student or not project or project.status != "active": return RedirectResponse("/projects", status_code=303)
    if db.scalar(select(Application).where(Application.student_id == student.id, Application.project_id == project_id)):
        return render(request, "project_detail.html", project=project, error="You have already applied to this project.")
    db.add(Application(student_id=student.id, project_id=project_id, message=message)); db.commit()
    return RedirectResponse("/student/dashboard", status_code=303)


@app.get("/startup/dashboard", response_class=HTMLResponse)
def startup_dashboard(request: Request, db: Session = Depends(get_db)):
    user, redirect = require_role(request, "startup")
    if redirect: return redirect
    profile = db.scalar(select(StartupProfile).where(StartupProfile.user_id == user["id"]))
    projects = db.scalars(select(Project).where(Project.startup_id == profile.id).order_by(Project.created_at.desc())).all() if profile else []
    applications = db.scalars(select(Application).options(joinedload(Application.student), joinedload(Application.project)).join(Project).where(Project.startup_id == profile.id)).all() if profile else []
    return render(request, "startup_dashboard.html", profile=profile, projects=projects, applications=applications)


@app.get("/startup/profile", response_class=HTMLResponse)
def startup_profile_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = require_role(request, "startup")
    if redirect: return redirect
    return render(request, "startup_profile.html", profile=db.scalar(select(StartupProfile).where(StartupProfile.user_id == user["id"])))


@app.post("/startup/profile")
def startup_profile(request: Request, company_name: str = Form(...), description: str = Form(""), website: str = Form(""), location: str = Form(""), industry: str = Form(""), innovation_zone: str = Form(""), contact_name: str = Form(""), db: Session = Depends(get_db)):
    user, redirect = require_role(request, "startup")
    if redirect: return redirect
    profile = db.scalar(select(StartupProfile).where(StartupProfile.user_id == user["id"]))
    values = locals(); fields = "company_name description website location industry innovation_zone contact_name".split()
    if profile: [setattr(profile, key, values[key]) for key in fields]
    else: db.add(StartupProfile(user_id=user["id"], **{key: values[key] for key in fields}))
    db.commit(); return RedirectResponse("/startup/dashboard", status_code=303)


@app.get("/startup/projects/new", response_class=HTMLResponse)
def new_project_page(request: Request):
    user, redirect = require_role(request, "startup")
    if redirect: return redirect
    return render(request, "project_form.html")


@app.post("/startup/projects/new")
def new_project(request: Request, title: str = Form(...), description: str = Form(...), required_skills: str = Form(""), preferred_fields: str = Form(""), project_duration: str = Form(""), location_type: str = Form("Remote"), compensation_type: str = Form("Unpaid / learning"), expected_deliverables: str = Form(""), db: Session = Depends(get_db)):
    user, redirect = require_role(request, "startup")
    if redirect: return redirect
    profile = db.scalar(select(StartupProfile).where(StartupProfile.user_id == user["id"]))
    if not profile: return RedirectResponse("/startup/profile", status_code=303)
    db.add(Project(startup_id=profile.id, title=title, description=description, required_skills=[x.strip() for x in required_skills.split(",") if x.strip()], preferred_fields=[x.strip() for x in preferred_fields.split(",") if x.strip()], project_duration=project_duration, location_type=location_type, compensation_type=compensation_type, expected_deliverables=expected_deliverables)); db.commit()
    return RedirectResponse("/startup/dashboard", status_code=303)


@app.post("/startup/applications/{application_id}")
def update_application(request: Request, application_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    user, redirect = require_role(request, "startup")
    if redirect: return redirect
    application = db.scalar(select(Application).options(joinedload(Application.project)).where(Application.id == application_id))
    profile = db.scalar(select(StartupProfile).where(StartupProfile.user_id == user["id"]))
    if application and profile and application.project.startup_id == profile.id and status in {"submitted", "shortlisted", "accepted", "rejected"}:
        application.status = status; db.commit()
    return RedirectResponse("/startup/dashboard", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, db: Session = Depends(get_db)):
    user, redirect = require_role(request, "admin")
    if redirect: return redirect
    stats = {"students": db.scalar(select(func.count(User.id)).where(User.role == "student")), "startups": db.scalar(select(func.count(User.id)).where(User.role == "startup")), "active_projects": db.scalar(select(func.count(Project.id)).where(Project.status == "active")), "applications": db.scalar(select(func.count(Application.id))), "closed_projects": db.scalar(select(func.count(Project.id)).where(Project.status == "closed"))}
    return render(request, "admin_dashboard.html", stats=stats)
