"""Employee management business logic."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.security import hash_password
from app.models.department import Department
from app.models.employee import Employee, EmployeeStatus, EmploymentType
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeSelfUpdate, EmployeeUpdate


def serialize_employee(emp: Employee) -> EmployeeResponse:
    """Convert an Employee ORM row to EmployeeResponse."""
    return EmployeeResponse(
        id=emp.id,
        user_id=emp.user_id,
        employee_code=emp.employee_code,
        first_name=emp.first_name,
        last_name=emp.last_name,
        full_name=emp.full_name,
        email=emp.email,
        phone=emp.phone,
        department_id=emp.department_id,
        department_name=emp.department.name if emp.department else None,
        job_title=emp.job_title,
        employment_type=emp.employment_type,
        status=emp.status,
        hire_date=emp.hire_date,
        base_salary=emp.base_salary,
        address=emp.address,
        emergency_contact=emp.emergency_contact,
        created_at=emp.created_at,
        updated_at=emp.updated_at,
    )


def _generate_employee_code(db: Session) -> str:
    max_id = db.scalar(select(func.max(Employee.id))) or 0
    seq = max_id + 1001
    while True:
        candidate = f"EMP-{seq}"
        exists = db.scalar(select(Employee.id).where(Employee.employee_code == candidate))
        if exists is None:
            return candidate
        seq += 1


def list_employees(
    db: Session,
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    status: Optional[EmployeeStatus] = None,
    employment_type: Optional[EmploymentType] = None,
    page: int = 1,
    page_size: int = 10,
) -> PaginatedResponse[EmployeeResponse]:
    """List employees with search, filters, and pagination."""
    stmt = select(Employee).options(joinedload(Employee.department))
    count_stmt = select(func.count(Employee.id))

    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Employee.first_name.ilike(term),
                Employee.last_name.ilike(term),
                Employee.email.ilike(term),
                Employee.employee_code.ilike(term),
                Employee.job_title.ilike(term),
            )
        )
    if department_id is not None:
        filters.append(Employee.department_id == department_id)
    if status is not None:
        filters.append(Employee.status == status)
    if employment_type is not None:
        filters.append(Employee.employment_type == employment_type)

    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(Employee.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return PaginatedResponse.create(
        items=[serialize_employee(emp) for emp in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_employee(db: Session, employee_id: int, current_user: User) -> EmployeeResponse:
    """Fetch employee details enforcing self-or-privileged access."""
    if current_user.role == UserRole.EMPLOYEE:
        if current_user.employee is None or current_user.employee.id != employee_id:
            raise ForbiddenException("You may only view your own employee profile")

    emp = db.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.id == employee_id)
    )
    if emp is None:
        raise NotFoundException("Employee not found")
    return serialize_employee(emp)


def create_employee(db: Session, payload: EmployeeCreate) -> EmployeeResponse:
    """Create a new employee record and optionally provision a linked User account."""
    normalized_email = payload.email.strip().lower()
    if db.scalar(select(Employee.id).where(func.lower(Employee.email) == normalized_email)):
        raise ConflictException("An employee with this email already exists")

    if payload.department_id is not None:
        if db.scalar(select(Department.id).where(Department.id == payload.department_id)) is None:
            raise NotFoundException("Specified department not found")

    code = payload.employee_code.strip().upper() if payload.employee_code else _generate_employee_code(db)
    if db.scalar(select(Employee.id).where(Employee.employee_code == code)):
        raise ConflictException(f"Employee code '{code}' is already in use")

    user_id = payload.user_id
    if user_id is not None:
        user = db.scalar(select(User).where(User.id == user_id))
        if user is None:
            raise NotFoundException("Linked user account not found")
        if db.scalar(select(Employee.id).where(Employee.user_id == user_id)):
            raise ConflictException("Specified user account is already linked to another employee")
    elif payload.create_user_account:
        if db.scalar(select(User.id).where(func.lower(User.email) == normalized_email)):
            raise ConflictException("A user account with this email already exists")
        new_user = User(
            email=normalized_email,
            full_name=f"{payload.first_name.strip()} {payload.last_name.strip()}",
            hashed_password=hash_password(payload.account_password),
            role=payload.account_role,
            is_active=payload.status == EmployeeStatus.ACTIVE,
        )
        db.add(new_user)
        db.flush()
        user_id = new_user.id

    emp = Employee(
        user_id=user_id,
        employee_code=code,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=normalized_email,
        phone=payload.phone,
        department_id=payload.department_id,
        job_title=payload.job_title.strip(),
        employment_type=payload.employment_type,
        status=payload.status,
        hire_date=payload.hire_date,
        base_salary=payload.base_salary,
        address=payload.address,
        emergency_contact=payload.emergency_contact,
    )
    db.add(emp)
    db.commit()

    created = db.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.id == emp.id)
    )
    return serialize_employee(created)


def update_employee(db: Session, employee_id: int, payload: EmployeeUpdate) -> EmployeeResponse:
    """Update employee details (Admin / HR Manager)."""
    emp = db.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.id == employee_id)
    )
    if emp is None:
        raise NotFoundException("Employee not found")

    if payload.email is not None:
        normalized_email = payload.email.strip().lower()
        conflict = db.scalar(
            select(Employee.id).where(
                func.lower(Employee.email) == normalized_email,
                Employee.id != employee_id,
            )
        )
        if conflict is not None:
            raise ConflictException("Another employee already uses this email")
        emp.email = normalized_email

    if "department_id" in payload.model_fields_set:
        if payload.department_id is not None:
            if db.scalar(select(Department.id).where(Department.id == payload.department_id)) is None:
                raise NotFoundException("Specified department not found")
        emp.department_id = payload.department_id

    for field in (
        "first_name",
        "last_name",
        "phone",
        "job_title",
        "employment_type",
        "status",
        "hire_date",
        "base_salary",
        "address",
        "emergency_contact",
    ):
        value = getattr(payload, field)
        if value is not None or field in {"phone", "address", "emergency_contact"} and field in payload.model_fields_set:
            setattr(emp, field, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(emp)
    emp = db.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.id == employee_id)
    )
    return serialize_employee(emp)


def update_own_profile(db: Session, employee: Employee, payload: EmployeeSelfUpdate) -> EmployeeResponse:
    """Allow an employee to update their own contact details."""
    fields_set = payload.model_fields_set
    if "phone" in fields_set:
        employee.phone = payload.phone
    if "address" in fields_set:
        employee.address = payload.address
    if "emergency_contact" in fields_set:
        employee.emergency_contact = payload.emergency_contact

    db.commit()
    refreshed = db.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.id == employee.id)
    )
    return serialize_employee(refreshed)


def deactivate_employee(db: Session, employee_id: int) -> EmployeeResponse:
    """Soft-deactivate an employee and disable any linked login account."""
    emp = db.scalar(
        select(Employee)
        .options(joinedload(Employee.department), joinedload(Employee.user))
        .where(Employee.id == employee_id)
    )
    if emp is None:
        raise NotFoundException("Employee not found")

    emp.status = EmployeeStatus.INACTIVE
    if emp.user is not None and emp.user.role != UserRole.ADMIN:
        emp.user.is_active = False

    db.commit()
    refreshed = db.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.id == employee_id)
    )
    return serialize_employee(refreshed)


def delete_employee(db: Session, employee_id: int) -> None:
    """Permanently delete an employee record, clearing department manager links safely."""
    emp = db.scalar(select(Employee).where(Employee.id == employee_id))
    if emp is None:
        raise NotFoundException("Employee not found")

    managed_depts = db.scalars(
        select(Department).where(Department.manager_id == employee_id)
    ).all()
    for dept in managed_depts:
        dept.manager_id = None

    db.delete(emp)
    db.commit()
