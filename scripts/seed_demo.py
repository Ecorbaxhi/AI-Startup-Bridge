from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Project, StartupProfile, StudentProfile, University, User

Base.metadata.create_all(engine)
db = SessionLocal()
if db.query(University).count():
    print('Demo data already exists.'); raise SystemExit
universities = [University(name='University of Tirana', city='Tirana'), University(name='Polytechnic University of Tirana', city='Tirana'), University(name='University of New York Tirana', city='Tirana')]
db.add_all(universities); db.flush()
for i in range(10):
    user = User(email=f'demo.student{i+1}@example.test', password_hash=hash_password('DemoOnly-ChangeMe'), role='student')
    db.add(user); db.flush(); db.add(StudentProfile(user_id=user.id, full_name=f'Fictional Student {i+1}', university_id=universities[i % 3].id, field_of_study=['Computer Science','Business Informatics','Agricultural Engineering'][i % 3], academic_year='Year 3', skills=[['Python','SQL'],['JavaScript','UX'],['Cybersecurity','Linux']][i % 3], interests=['AI','innovation'], bio='Fictional demo profile.', availability='Part-time'))
for i in range(5):
    user = User(email=f'demo.startup{i+1}@example.test', password_hash=hash_password('DemoOnly-ChangeMe'), role='startup'); db.add(user); db.flush(); startup = StartupProfile(user_id=user.id, company_name=f'Fictional Tech Studio {i+1}', description='Fictional demonstration startup; not an official tenant or partner.', location='Albania', industry=['AI','cybersecurity','fintech','software','agritech'][i], innovation_zone='TEDA Tirana' if i == 0 else 'Elsewhere in Albania', contact_name='Demo Contact'); db.add(startup); db.flush(); db.add_all([Project(startup_id=startup.id, title=f'Demo {startup.industry} project {j+1}', description='A fictional project for demonstrating the bridge workflow.', required_skills=[['Python','SQL'],['JavaScript','UX']][j % 2], preferred_fields=['Computer Science'], project_duration='8 weeks', location_type='Hybrid', compensation_type='Unpaid / learning', expected_deliverables='A documented prototype.') for j in range(2)])
db.commit(); print('Seeded fictional demo data. Demo password: DemoOnly-ChangeMe (local use only).')
