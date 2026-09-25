import os
os.environ['DATABASE_URL'] = 'sqlite:///./test_bridge.db'
os.environ['SESSION_SECRET_KEY'] = 'test-secret'
from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app
from app.matching import match_student_project
from app.models import Project, StudentProfile


def setup_function():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)


def test_health_and_registration():
    with TestClient(app) as client:
        assert client.get('/health').json() == {'status': 'ok'}
        response = client.post('/register', data={'email': 'student@test.local', 'password': 'password123', 'role': 'student'}, follow_redirects=False)
        assert response.status_code == 303
        assert client.get('/student/dashboard').status_code == 200


def test_role_authorization():
    with TestClient(app) as client:
        client.post('/register', data={'email': 'startup@test.local', 'password': 'password123', 'role': 'startup'})
        assert client.get('/student/profile', follow_redirects=False).status_code == 303
        assert client.get('/startup/dashboard').status_code == 200


def test_matching_missing_skills():
    student = StudentProfile(full_name='A', field_of_study='Computer Science', skills=['Python'], interests=['AI'], availability='Part-time')
    project = Project(title='AI', description='AI project', required_skills=['Python', 'SQL'], preferred_fields=['Computer Science'], project_duration='Part-time')
    result = match_student_project(student, project)
    assert result['score'] > 0
    assert result['matching_skills'] == ['python']
    assert result['missing_skills'] == ['sql']
