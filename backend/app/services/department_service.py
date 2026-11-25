"""Department management business logic."""

from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.common import PaginatedResponse
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate


def _serialize_department(dept: Department, employee_count: int) -> DepartmentResponse:
    manager_name = dept.manager.full_name if dept.manager else None
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        manager_id=dept.manager_id,
        manager_name=manager_name,
        employee_count=employee_count,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


def _get_employee_counts(db: Session, department_ids: List[int]) -> dict[int, int]:
    if not department_ids:
        return {}
    rows = db.execute(
        select(Employee.department_id, func.count(Employee.id))
        .where(Employee.department_id.in_(department_ids))
        .group_by(Employee.department_id)
    ).all()
    return {dept_id: count for dept_id, count in rows if dept_id is not None}


def list_departments(
    db: Session,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[DepartmentResponse]:
    """Return paginated departments with employee headcount."""
    stmt = select(Department).options(joinedload(Department.manager))
    count_stmt = select(func.count(Department.id))

    if search:
        term = f"%{search.strip()}%"
        condition = or_(Department.name.ilike(term), Department.code.ilike(term))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = db.scalar(count_stmt) or 0
    departments = db.scalars(
        stmt.order_by(Department.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    counts = _get_employee_counts(db, [d.id for d in departments])
    items = [_serialize_department(d, counts.get(d.id, 0)) for d in departments]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


def get_department(db: Session, department_id: int) -> DepartmentResponse:
    """Retrieve a single department by ID."""
    dept = db.scalar(
        select(Department)
        .options(joinedload(Department.manager))
        .where(Department.id == department_id)
    )
    if dept is None:
        raise NotFoundException("Department not found")

    counts = _get_employee_counts(db, [dept.id])
    return _serialize_department(dept, counts.get(dept.id, 0))


def _validate_manager(db: Session, manager_id: Optional[int]) -> None:
    if manager_id is not None:
        exists = db.scalar(select(Employee.id).where(Employee.id == manager_id))
        if exists is None:
            raise NotFoundException(f"Manager employee with id {manager_id} not found")


def create_department(db: Session, payload: DepartmentCreate) -> DepartmentResponse:
    """Create a new department validating uniqueness of name and code."""
    existing = db.scalar(
        select(Department).where(
            or_(
                func.lower(Department.name) == payload.name.lower(),
                func.lower(Department.code) == payload.code.lower(),
            )
        )
    )
    if existing is not None:
        raise ConflictException("A department with this name or code already exists")

    _validate_manager(db, payload.manager_id)

    dept = Department(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        manager_id=payload.manager_id,
    )
    db.add(dept)
    db.commit()
    return get_department(db, dept.id)


def update_department(db: Session, department_id: int, payload: DepartmentUpdate) -> DepartmentResponse:
    """Update department attributes."""
    dept = db.scalar(select(Department).where(Department.id == department_id))
    if dept is None:
        raise NotFoundException("Department not found")

    if payload.name is not None:
        conflict = db.scalar(
            select(Department.id).where(
                func.lower(Department.name) == payload.name.lower(),
                Department.id != department_id,
            )
        )
        if conflict is not None:
            raise ConflictException("Department name already in use")
        dept.name = payload.name

    if payload.code is not None:
        conflict = db.scalar(
            select(Department.id).where(
                func.lower(Department.code) == payload.code.lower(),
                Department.id != department_id,
            )
        )
        if conflict is not None:
            raise ConflictException("Department code already in use")
        dept.code = payload.code

    fields_set = payload.model_fields_set
    if "description" in fields_set:
        dept.description = payload.description
    if "manager_id" in fields_set:
        _validate_manager(db, payload.manager_id)
        dept.manager_id = payload.manager_id

    db.commit()
    return get_department(db, dept.id)


def delete_department(db: Session, department_id: int) -> None:
    """Delete a department only when no employees are currently assigned to it."""
    dept = db.scalar(select(Department).where(Department.id == department_id))
    if dept is None:
        raise NotFoundException("Department not found")

    assigned_count = db.scalar(
        select(func.count(Employee.id)).where(Employee.department_id == department_id)
    ) or 0
    if assigned_count > 0:
        raise ConflictException(
            f"Cannot delete department '{dept.name}' because {assigned_count} employee(s) are assigned to it"
        )

    db.delete(dept)
    db.commit()


def assign_employees_to_department(
    db: Session,
    department_id: int,
    employee_ids: List[int],
) -> DepartmentResponse:
    """Assign a list of employees to the specified department."""
    dept = db.scalar(select(Department).where(Department.id == department_id))
    if dept is None:
        raise NotFoundException("Department not found")

    employees = db.scalars(select(Employee).where(Employee.id.in_(employee_ids))).all()
    if len(employees) != len(set(employee_ids)):
        raise NotFoundException("One or more specified employees were not found")

    for emp in employees:
        emp.department_id = department_id

    db.commit()
    return get_department(db, department_id)
