"""Salary management and payroll reporting endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.salary import PaymentStatus
from app.models.user import User, UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.salary import SalaryCreate, SalaryResponse, SalarySummaryResponse, SalaryUpdate
from app.services import salary_service

router = APIRouter(prefix="/salaries", tags=["Salary Management"])


@router.get("/summary", response_model=SalarySummaryResponse)
def get_salary_summary(
    pay_month: Optional[int] = Query(default=None, ge=1, le=12),
    pay_year: Optional[int] = Query(default=None, ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SalarySummaryResponse:
    """Get aggregated salary summary scoped to caller permissions."""
    return salary_service.get_salary_summary(db, current_user, pay_month=pay_month, pay_year=pay_year)


@router.get("", response_model=PaginatedResponse[SalaryResponse])
def list_salaries(
    employee_id: Optional[int] = Query(default=None, ge=1),
    pay_month: Optional[int] = Query(default=None, ge=1, le=12),
    pay_year: Optional[int] = Query(default=None, ge=2000, le=2100),
    payment_status: Optional[PaymentStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SalaryResponse]:
    """List salary records (Employee sees only own records; Admin/HR see all)."""
    return salary_service.list_salaries(
        db,
        current_user=current_user,
        employee_id=employee_id,
        pay_month=pay_month,
        pay_year=pay_year,
        payment_status=payment_status,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=SalaryResponse, status_code=status.HTTP_201_CREATED)
def create_salary(
    payload: SalaryCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> SalaryResponse:
    """Create a monthly salary record (Admin / HR Manager)."""
    return salary_service.create_salary_record(db, current_user, payload)


@router.put("/{salary_id}", response_model=SalaryResponse)
def update_salary(
    salary_id: int,
    payload: SalaryUpdate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> SalaryResponse:
    """Update a salary record and recompute net salary (Admin / HR Manager)."""
    return salary_service.update_salary_record(db, salary_id, payload)


@router.delete("/{salary_id}", response_model=MessageResponse)
def delete_salary(
    salary_id: int,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Delete a salary record (Admin only)."""
    salary_service.delete_salary_record(db, salary_id)
    return MessageResponse(message="Salary record deleted successfully")
