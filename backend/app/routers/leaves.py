"""Leave application, listing, cancellation, and approval endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.leave import LeaveStatus, LeaveType
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.leave import LeaveCreate, LeaveResponse, LeaveReviewRequest
from app.services import leave_service

router = APIRouter(prefix="/leaves", tags=["Leave Management"])


@router.post("", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
def apply_leave(
    payload: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LeaveResponse:
    """Submit a new leave request."""
    return leave_service.apply_leave(db, current_user, payload)


@router.get("", response_model=PaginatedResponse[LeaveResponse])
def list_leaves(
    employee_id: Optional[int] = Query(default=None, ge=1),
    status_filter: Optional[LeaveStatus] = Query(default=None, alias="status"),
    leave_type: Optional[LeaveType] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[LeaveResponse]:
    """List leave requests (Employee sees own; Admin/HR see all)."""
    return leave_service.list_leaves(
        db,
        current_user=current_user,
        employee_id=employee_id,
        status=status_filter,
        leave_type=leave_type,
        page=page,
        page_size=page_size,
    )


@router.patch("/{leave_id}/review", response_model=LeaveResponse)
def review_leave(
    leave_id: int,
    payload: LeaveReviewRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> LeaveResponse:
    """Approve or reject a pending leave request (Admin / HR Manager)."""
    return leave_service.review_leave(db, leave_id, current_user, payload)


@router.post("/{leave_id}/cancel", response_model=LeaveResponse)
def cancel_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LeaveResponse:
    """Cancel a pending leave request."""
    return leave_service.cancel_leave(db, leave_id, current_user)
