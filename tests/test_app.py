import os
import re

os.environ["DATABASE_URL"] = "sqlite:///./test_bridge.db"
os.environ["SESSION_SECRET_KEY"] = "test-secret"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient
from app.database import Base, SessionLocal, engine
from app.main import app
from app.matching import match_student_project
from app.auth import hash_password
from app.models import Project, StudentProfile, University, User


def csrf(client, path):
    page = client.get(path)
    match = re.search(r'name="csrf" value="([^"]+)"', page.text)
    assert match, f"No CSRF token on {path}"
    return match.group(1)


def setup_function():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    db.add(University(name="University of Tirana", city="Tirana"))
    db.commit()
    db.close()


def test_health_registration_and_csrf():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.post("/register", data={"email": "bad@test.local", "password": "password123", "role": "student"}, follow_redirects=False).status_code == 422
        token = csrf(client, "/register")
        response = client.post("/register", data={"csrf": token, "email": "student@test.local", "password": "password123", "role": "student"}, follow_redirects=False)
        assert response.status_code == 303
        assert client.get("/student/dashboard").status_code == 200


def test_role_authorization_and_student_profile():
    with TestClient(app) as client:
        token = csrf(client, "/register")
        client.post("/register", data={"csrf": token, "email": "student2@test.local", "password": "password123", "role": "student"})
        assert client.get("/startup/dashboard", follow_redirects=False).status_code == 303
        token = csrf(client, "/student/profile")
        response = client.post("/student/profile", data={"csrf": token, "full_name": "Student Two", "university_id": "1", "field_of_study": "Computer Science", "skills": "Python, SQL", "interests": "AI", "availability": "Part-time", "discovery_enabled": "on"}, follow_redirects=False)
        assert response.status_code == 303
        profile = SessionLocal().query(StudentProfile).filter_by(full_name="Student Two").one()
        assert profile.discovery_enabled is True


def test_startup_project_lifecycle_and_application_flow():
    with TestClient(app) as startup:
        token = csrf(startup, "/register")
        startup.post("/register", data={"csrf": token, "email": "startup@test.local", "password": "password123", "role": "startup"})
        token = csrf(startup, "/startup/profile")
        startup.post("/startup/profile", data={"csrf": token, "company_name": "Bridge Labs", "industry": "AI", "innovation_zone": "TEDA Tirana"})
        token = csrf(startup, "/startup/projects/new")
        response = startup.post("/startup/projects/new", data={"csrf": token, "title": "AI prototype", "description": "Build an AI prototype", "required_skills": "Python, SQL", "preferred_fields": "Computer Science", "project_duration": "8 weeks"}, follow_redirects=False)
        assert response.status_code == 303
    db = SessionLocal(); project = db.query(Project).one(); project_id = project.id; db.close()

    with TestClient(app) as student:
        token = csrf(student, "/register")
        student.post("/register", data={"csrf": token, "email": "applicant@test.local", "password": "password123", "role": "student"})
        token = csrf(student, "/student/profile")
        student.post("/student/profile", data={"csrf": token, "full_name": "Applicant", "field_of_study": "Computer Science", "skills": "Python"})
        token = csrf(student, f"/projects/{project_id}")
        assert student.post(f"/projects/{project_id}/apply", data={"csrf": token, "message": "I would like to contribute."}, follow_redirects=False).status_code == 303
        token = csrf(student, f"/projects/{project_id}")
        duplicate = student.post(f"/projects/{project_id}/apply", data={"csrf": token, "message": "Again"})
        assert "already applied" in duplicate.text

    with TestClient(app) as startup:
        token = csrf(startup, "/login")
        startup.post("/login", data={"csrf": token, "email": "startup@test.local", "password": "password123"})
        assert startup.get("/startup/dashboard").status_code == 200
        db = SessionLocal(); project = db.query(Project).one(); db.close()
        token = csrf(startup, f"/startup/projects/{project_id}/edit")
        startup.post(f"/startup/projects/{project_id}/edit", data={"csrf": token, "title": "Updated AI prototype", "description": "Updated description"})
        token = csrf(startup, "/startup/dashboard")
        startup.post(f"/startup/projects/{project_id}/status", data={"csrf": token, "status": "closed"})
        db = SessionLocal(); assert db.query(Project).one().status == "closed"; db.close()


def test_matching_and_discovery_opt_out():
    student = StudentProfile(full_name="A", field_of_study="Computer Science", skills=["Python"], interests=["AI"], availability="Part-time")
    project = Project(title="AI", description="AI project", required_skills=["Python", "SQL"], preferred_fields=["Computer Science"], project_duration="Part-time")
    result = match_student_project(student, project)
    assert result["matching_skills"] == ["python"]
    assert result["missing_skills"] == ["sql"]
    assert result["score"] > 0


def test_admin_route_is_protected():
    with TestClient(app) as client:
        token = csrf(client, "/register")
        client.post("/register", data={"csrf": token, "email": "student3@test.local", "password": "password123", "role": "student"})
        assert client.get("/admin", follow_redirects=False).status_code == 303
    db = SessionLocal()
    db.add(User(email="admin@test.local", password_hash=hash_password("admin-password-123"), role="admin"))
    db.commit()
    db.close()
    with TestClient(app) as client:
        token = csrf(client, "/login")
        client.post("/login", data={"csrf": token, "email": "admin@test.local", "password": "admin-password-123"})
        assert client.get("/admin").status_code == 200
