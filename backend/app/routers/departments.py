"""Department management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.department import (
    DepartmentAssignEmployeesRequest,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.services import department_service

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=PaginatedResponse[DepartmentResponse])
def list_departments(
    search: Optional[str] = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[DepartmentResponse]:
    """List departments with employee counts."""
    return department_service.list_departments(db, search=search, page=page, page_size=page_size)


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    """Get a single department by ID."""
    return department_service.get_department(db, department_id)


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    """Create a department (Admin / HR Manager)."""
    return department_service.create_department(db, payload)


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    """Update department details (Admin / HR Manager)."""
    return department_service.update_department(db, department_id, payload)


@router.delete("/{department_id}", response_model=MessageResponse)
def delete_department(
    department_id: int,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Delete a department when no employees are assigned to it."""
    department_service.delete_department(db, department_id)
    return MessageResponse(message="Department deleted successfully")


@router.post("/{department_id}/assign-employees", response_model=DepartmentResponse)
def assign_employees(
    department_id: int,
    payload: DepartmentAssignEmployeesRequest,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    """Bulk-assign employees to a department."""
    return department_service.assign_employees_to_department(db, department_id, payload.employee_ids)
