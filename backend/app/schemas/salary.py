"""Salary record and payroll summary schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.salary import PaymentStatus


class SalaryCreate(BaseModel):
    """Create a monthly salary record (net_salary is computed server-side)."""

    employee_id: int = Field(..., ge=1)
    pay_month: int = Field(..., ge=1, le=12)
    pay_year: int = Field(..., ge=2000, le=2100)
    basic_salary: Decimal = Field(..., ge=0)
    allowances: Decimal = Field(default=Decimal("0.00"), ge=0)
    deductions: Decimal = Field(default=Decimal("0.00"), ge=0)
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_net_salary_non_negative(self) -> "SalaryCreate":
        if self.basic_salary + self.allowances < self.deductions:
            raise ValueError("Deductions cannot exceed basic salary plus allowances")
        return self


class SalaryUpdate(BaseModel):
    """Update an existing salary record."""

    basic_salary: Optional[Decimal] = Field(default=None, ge=0)
    allowances: Optional[Decimal] = Field(default=None, ge=0)
    deductions: Optional[Decimal] = Field(default=None, ge=0)
    payment_status: Optional[PaymentStatus] = None
    payment_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)


class SalaryResponse(BaseModel):
    """Serialized salary record with employee details."""

    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    pay_month: int
    pay_year: int
    basic_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    net_salary: Decimal
    payment_status: PaymentStatus
    payment_date: Optional[date] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalarySummaryResponse(BaseModel):
    """Payroll totals for reporting and dashboard widgets."""

    total_records: int
    total_basic_salary: Decimal
    total_allowances: Decimal
    total_deductions: Decimal
    total_net_payroll: Decimal
    paid_count: int
    pending_count: int
