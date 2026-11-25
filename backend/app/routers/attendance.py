"""Attendance check-in, check-out, history, and reporting endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.attendance import AttendanceStatus
from app.models.user import User, UserRole
from app.schemas.attendance import (
    AttendanceRecordCreate,
    AttendanceReportSummary,
    AttendanceResponse,
    CheckInRequest,
    CheckOutRequest,
)
from app.schemas.common import PaginatedResponse
from app.services import attendance_service

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_in(
    payload: CheckInRequest = CheckInRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttendanceResponse:
    """Check in for the current date."""
    return attendance_service.check_in(db, current_user, payload)


@router.post("/check-out", response_model=AttendanceResponse)
def check_out(
    payload: CheckOutRequest = CheckOutRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttendanceResponse:
    """Check out for the current date and calculate worked hours."""
    return attendance_service.check_out(db, current_user, payload)


@router.post("", response_model=AttendanceResponse)
def record_manual_attendance(
    payload: AttendanceRecordCreate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR_MANAGER)),
    db: Session = Depends(get_db),
) -> AttendanceResponse:
    """Create or update an attendance record manually (Admin / HR Manager)."""
    return attendance_service.upsert_manual_attendance(db, payload)


@router.get("", response_model=PaginatedResponse[AttendanceResponse])
def list_attendance(
    employee_id: Optional[int] = Query(default=None, ge=1),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    status_filter: Optional[AttendanceStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AttendanceResponse]:
    """List attendance records scoped by role."""
    return attendance_service.list_attendance(
        db,
        current_user=current_user,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        status=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get("/report", response_model=AttendanceReportSummary)
def get_attendance_report(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    department_id: Optional[int] = Query(default=None, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttendanceReportSummary:
    """Generate aggregated attendance statistics for a date window."""
    return attendance_service.get_attendance_report(
        db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
    )
