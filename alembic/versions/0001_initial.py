from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('email', sa.String(255), nullable=False), sa.Column('password_hash', sa.String(255), nullable=False), sa.Column('role', sa.String(20), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False), sa.UniqueConstraint('email'))
    op.create_index('ix_users_email', 'users', ['email'], unique=False); op.create_index('ix_users_role', 'users', ['role'], unique=False)
    op.create_table('universities', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(200), nullable=False), sa.Column('city', sa.String(100), nullable=False), sa.UniqueConstraint('name'))
    op.create_table('student_profiles', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False), sa.Column('full_name', sa.String(160), nullable=False), sa.Column('university_id', sa.Integer(), sa.ForeignKey('universities.id')), sa.Column('field_of_study', sa.String(160), nullable=False), sa.Column('academic_year', sa.String(40), nullable=False), sa.Column('skills', sa.JSON(), nullable=False), sa.Column('interests', sa.JSON(), nullable=False), sa.Column('bio', sa.Text(), nullable=False), sa.Column('availability', sa.String(100), nullable=False), sa.Column('discovery_enabled', sa.Boolean(), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False), sa.UniqueConstraint('user_id'))
    op.create_table('startup_profiles', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False), sa.Column('company_name', sa.String(200), nullable=False), sa.Column('description', sa.Text(), nullable=False), sa.Column('website', sa.String(255), nullable=False), sa.Column('location', sa.String(160), nullable=False), sa.Column('industry', sa.String(120), nullable=False), sa.Column('innovation_zone', sa.String(160), nullable=False), sa.Column('contact_name', sa.String(160), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False), sa.UniqueConstraint('user_id'))
    op.create_table('projects', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('startup_id', sa.Integer(), sa.ForeignKey('startup_profiles.id'), nullable=False), sa.Column('title', sa.String(200), nullable=False), sa.Column('description', sa.Text(), nullable=False), sa.Column('required_skills', sa.JSON(), nullable=False), sa.Column('preferred_fields', sa.JSON(), nullable=False), sa.Column('project_duration', sa.String(100), nullable=False), sa.Column('location_type', sa.String(100), nullable=False), sa.Column('compensation_type', sa.String(100), nullable=False), sa.Column('compensation_details', sa.String(255), nullable=False), sa.Column('expected_deliverables', sa.Text(), nullable=False), sa.Column('status', sa.String(30), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False))
    op.create_index('ix_projects_startup_id', 'projects', ['startup_id'], unique=False); op.create_index('ix_projects_status', 'projects', ['status'], unique=False)
    op.create_table('applications', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False), sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False), sa.Column('status', sa.String(30), nullable=False), sa.Column('message', sa.Text(), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False), sa.UniqueConstraint('student_id', 'project_id', name='uq_student_project'))
    op.create_index('ix_applications_student_id', 'applications', ['student_id'], unique=False); op.create_index('ix_applications_project_id', 'applications', ['project_id'], unique=False)

def downgrade():
    op.drop_table('applications'); op.drop_table('projects'); op.drop_table('startup_profiles'); op.drop_table('student_profiles'); op.drop_table('universities'); op.drop_table('users')
