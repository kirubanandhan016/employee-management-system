"""Leave request and approval workflow schemas."""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.leave import LeaveStatus, LeaveType


class LeaveCreate(BaseModel):
    """Schema for applying for leave."""

    employee_id: Optional[int] = Field(default=None, ge=1)
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=5, max_length=1000)

    @model_validator(mode="after")
    def validate_dates(self) -> "LeaveCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class LeaveReviewRequest(BaseModel):
    """HR/Admin approval or rejection payload."""

    status: Literal["approved", "rejected"]
    review_comment: Optional[str] = Field(default=None, max_length=500)


class LeaveResponse(BaseModel):
    """Serialized leave request."""

    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    leave_type: LeaveType
    start_date: date
    end_date: date
    days_count: int
    reason: str
    status: LeaveStatus
    reviewed_by: Optional[int] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
