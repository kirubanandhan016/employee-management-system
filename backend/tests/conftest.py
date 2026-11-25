"""Pytest fixtures and test database setup."""

from collections.abc import Generator
from datetime import date
from decimal import Decimal
import os

# Ensure settings resolve cleanly in test mode before importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-characters-long"

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.database import get_db
from app.main import app
from app.models import Base
from app.models.department import Department
from app.models.employee import Employee, EmployeeStatus, EmploymentType
from app.models.user import User, UserRole

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(TEST_ENGINE, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE, class_=Session)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Create fresh database tables for each test function."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient wired to the isolated test DB session."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_actors(db_session: Session) -> dict:
    """Create Admin, HR Manager, and two Employees with a default department."""
    dept = Department(name="Engineering", code="ENG", description="Engineering Department")
    db_session.add(dept)
    db_session.flush()

    admin_user = User(
        email="admin@test.com",
        full_name="Admin User",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    hr_user = User(
        email="hr@test.com",
        full_name="HR Manager",
        hashed_password=hash_password("HrPass@123"),
        role=UserRole.HR_MANAGER,
        is_active=True,
    )
    emp_user = User(
        email="emp1@test.com",
        full_name="Alice Employee",
        hashed_password=hash_password("EmpPass@123"),
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    emp2_user = User(
        email="emp2@test.com",
        full_name="Bob Employee",
        hashed_password=hash_password("EmpPass@123"),
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    db_session.add_all([admin_user, hr_user, emp_user, emp2_user])
    db_session.flush()

    emp1 = Employee(
        user_id=emp_user.id,
        employee_code="EMP-2001",
        first_name="Alice",
        last_name="Employee",
        email="emp1@test.com",
        department_id=dept.id,
        job_title="Software Engineer",
        employment_type=EmploymentType.FULL_TIME,
        status=EmployeeStatus.ACTIVE,
        hire_date=date(2024, 1, 10),
        base_salary=Decimal("6000.00"),
    )
    emp2 = Employee(
        user_id=emp2_user.id,
        employee_code="EMP-2002",
        first_name="Bob",
        last_name="Employee",
        email="emp2@test.com",
        department_id=dept.id,
        job_title="QA Engineer",
        employment_type=EmploymentType.FULL_TIME,
        status=EmployeeStatus.ACTIVE,
        hire_date=date(2024, 2, 15),
        base_salary=Decimal("5200.00"),
    )
    db_session.add_all([emp1, emp2])
    db_session.commit()

    return {
        "department": dept,
        "admin": admin_user,
        "hr": hr_user,
        "emp1_user": emp_user,
        "emp2_user": emp2_user,
        "emp1": emp1,
        "emp2": emp2,
        "admin_headers": {"Authorization": f"Bearer {create_access_token(admin_user.id, admin_user.role.value)}"},
        "hr_headers": {"Authorization": f"Bearer {create_access_token(hr_user.id, hr_user.role.value)}"},
        "emp1_headers": {"Authorization": f"Bearer {create_access_token(emp_user.id, emp_user.role.value)}"},
        "emp2_headers": {"Authorization": f"Bearer {create_access_token(emp2_user.id, emp2_user.role.value)}"},
    }
