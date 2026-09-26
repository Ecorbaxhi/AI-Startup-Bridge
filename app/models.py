from datetime import datetime, timezone
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    student_profile: Mapped["StudentProfile | None"] = relationship(back_populates="user", uselist=False)
    startup_profile: Mapped["StartupProfile | None"] = relationship(back_populates="user", uselist=False)


class University(Base):
    __tablename__ = "universities"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    city: Mapped[str] = mapped_column(String(100))
    students: Mapped[list["StudentProfile"]] = relationship(back_populates="university")


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    full_name: Mapped[str] = mapped_column(String(160))
    university_id: Mapped[int | None] = mapped_column(ForeignKey("universities.id"))
    field_of_study: Mapped[str] = mapped_column(String(160), default="")
    academic_year: Mapped[str] = mapped_column(String(40), default="")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    interests: Mapped[list] = mapped_column(JSON, default=list)
    bio: Mapped[str] = mapped_column(Text, default="")
    availability: Mapped[str] = mapped_column(String(100), default="")
    discovery_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    user: Mapped[User] = relationship(back_populates="student_profile")
    university: Mapped["University | None"] = relationship(back_populates="students")
    applications: Mapped[list["Application"]] = relationship(back_populates="student")


class StartupProfile(Base):
    __tablename__ = "startup_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    company_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(160), default="")
    industry: Mapped[str] = mapped_column(String(120), default="")
    innovation_zone: Mapped[str] = mapped_column(String(160), default="")
    contact_name: Mapped[str] = mapped_column(String(160), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    user: Mapped[User] = relationship(back_populates="startup_profile")
    projects: Mapped[list["Project"]] = relationship(back_populates="startup")


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    startup_id: Mapped[int] = mapped_column(ForeignKey("startup_profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    required_skills: Mapped[list] = mapped_column(JSON, default=list)
    preferred_fields: Mapped[list] = mapped_column(JSON, default=list)
    project_duration: Mapped[str] = mapped_column(String(100), default="")
    location_type: Mapped[str] = mapped_column(String(100), default="Remote")
    compensation_type: Mapped[str] = mapped_column(String(100), default="Unpaid / learning")
    compensation_details: Mapped[str] = mapped_column(String(255), default="")
    expected_deliverables: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    startup: Mapped[StartupProfile] = relationship(back_populates="projects")
    applications: Mapped[list["Application"]] = relationship(back_populates="project")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("student_id", "project_id", name="uq_student_project"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="submitted")
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    student: Mapped[StudentProfile] = relationship(back_populates="applications")
    project: Mapped[Project] = relationship(back_populates="applications")
