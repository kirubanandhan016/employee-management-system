"""Attendance check-in, check-out, history, and reporting schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.attendance import AttendanceStatus


class CheckInRequest(BaseModel):
    """Employee check-in payload."""

    employee_id: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = Field(default=None, max_length=500)


class CheckOutRequest(BaseModel):
    """Employee check-out payload."""

    employee_id: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = Field(default=None, max_length=500)


class AttendanceRecordCreate(BaseModel):
    """Admin/HR manual attendance entry or correction."""

    employee_id: int = Field(..., ge=1)
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: Optional[str] = Field(default=None, max_length=500)


class AttendanceResponse(BaseModel):
    """Serialized attendance record."""

    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: AttendanceStatus
    work_hours: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceReportSummary(BaseModel):
    """Aggregated attendance report metrics for a date range."""

    start_date: date
    end_date: date
    total_records: int
    present_count: int
    late_count: int
    half_day_count: int
    absent_count: int
    on_leave_count: int
    average_work_hours: float
