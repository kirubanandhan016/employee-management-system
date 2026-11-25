"""Employee CRUD and filtering schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.employee import EmployeeStatus, EmploymentType
from app.models.user import UserRole


class EmployeeBase(BaseModel):
    """Shared employee attributes."""

    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    department_id: Optional[int] = Field(default=None, ge=1)
    job_title: str = Field(..., min_length=2, max_length=120)
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    hire_date: date
    base_salary: Decimal = Field(..., ge=0)
    address: Optional[str] = Field(default=None, max_length=500)
    emergency_contact: Optional[str] = Field(default=None, max_length=150)


class EmployeeCreate(EmployeeBase):
    """Schema to onboard a new employee, optionally creating a linked login account."""

    employee_code: Optional[str] = Field(default=None, min_length=2, max_length=30)
    user_id: Optional[int] = Field(default=None, ge=1)
    create_user_account: bool = False
    account_password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    account_role: UserRole = UserRole.EMPLOYEE

    @model_validator(mode="after")
    def validate_account_creation(self) -> "EmployeeCreate":
        if self.create_user_account and not self.account_password:
            raise ValueError("account_password is required when create_user_account is true")
        if self.create_user_account and self.user_id is not None:
            raise ValueError("Cannot provide both user_id and create_user_account=true")
        return self


class EmployeeUpdate(BaseModel):
    """Schema to update employee details."""

    first_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    department_id: Optional[int] = Field(default=None, ge=1)
    job_title: Optional[str] = Field(default=None, min_length=2, max_length=120)
    employment_type: Optional[EmploymentType] = None
    status: Optional[EmployeeStatus] = None
    hire_date: Optional[date] = None
    base_salary: Optional[Decimal] = Field(default=None, ge=0)
    address: Optional[str] = Field(default=None, max_length=500)
    emergency_contact: Optional[str] = Field(default=None, max_length=150)


class EmployeeSelfUpdate(BaseModel):
    """Restricted fields an employee may update on their own profile."""

    phone: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=500)
    emergency_contact: Optional[str] = Field(default=None, max_length=150)


class EmployeeResponse(BaseModel):
    """Full serialized employee response."""

    id: int
    user_id: Optional[int] = None
    employee_code: str
    first_name: str
    last_name: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    job_title: str
    employment_type: EmploymentType
    status: EmployeeStatus
    hire_date: date
    base_salary: Decimal
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
