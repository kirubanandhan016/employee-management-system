"""Employee directory, onboarding, profile, and lifecycle endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_employee, get_current_user, require_roles
from app.models.employee import Employee, EmployeeStatus, EmploymentType
from app.models.user import User, UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeSelfUpdate, EmployeeUpdate
from app.services import employee_service

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("/me", response_model=EmployeeResponse)
def get_my_employee_profile(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployeeResponse:
    """Get the authenticated user's own employee profile."""
    return employee_service.get_employee(db, current_employee.id, current_user)


@router.patch("/me", response_model=EmployeeResponse)
def update_my_employee_profile(
    payload: EmployeeSelfUpdate,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    """Update personal contact details on the authenticated employee's own profile."""
    return employee_service.update_own_profile(db, current_employee, payload)


@router.get("", response_model=PaginatedResponse[EmployeeResponse])
def list_employees(
    search: Optional[str] = Query(default=None, max_length=100),
    department_id: Optional[int] = Query(default=None, ge=1),
    status_filter: Optional[EmployeeStatus] = Query(default=None, alias="status"),
    employment_type: Optional[EmploymentType] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> PaginatedResponse[EmployeeResponse]:
    """Search, filter, and paginate company employees (Admin / HR Manager)."""
    return employee_service.list_employees(
        db,
        search=search,
        department_id=department_id,
        status=status_filter,
        employment_type=employment_type,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    """Create a new employee record (Admin / HR Manager)."""
    return employee_service.create_employee(db, payload)


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    """View employee details (Admin/HR or the employee themselves)."""
    return employee_service.get_employee(db, employee_id, current_user)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    """Update employee information (Admin / HR Manager)."""
    return employee_service.update_employee(db, employee_id, payload)


@router.post("/{employee_id}/deactivate", response_model=EmployeeResponse)
def deactivate_employee(
    employee_id: int,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    """Soft-deactivate an employee record (Admin / HR Manager)."""
    return employee_service.deactivate_employee(db, employee_id)


@router.delete("/{employee_id}", response_model=MessageResponse)
def delete_employee(
    employee_id: int,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Permanently delete an employee record (Admin / HR Manager)."""
    employee_service.delete_employee(db, employee_id)
    return MessageResponse(message="Employee deleted successfully")
