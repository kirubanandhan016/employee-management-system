"""Dashboard analytics response schemas."""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.attendance import AttendanceResponse
from app.schemas.leave import LeaveResponse
from app.schemas.salary import SalaryResponse


class DepartmentStat(BaseModel):
    """Employee count and salary budget by department."""

    department_id: int
    department_name: str
    department_code: str
    employee_count: int
    total_base_salary: Decimal


class AttendanceTrendPoint(BaseModel):
    """Daily attendance breakdown for dashboard charts."""

    date: str
    present: int
    late: int
    absent: int
    on_leave: int


class MonthlyPayrollPoint(BaseModel):
    """Monthly payroll expense trend point."""

    period: str
    total_net_salary: Decimal
    paid_amount: Decimal
    record_count: int


class DashboardOverviewResponse(BaseModel):
    """Unified dashboard payload tailored to the caller's role."""

    role: str
    total_employees: int
    active_employees: int
    inactive_employees: int
    total_departments: int
    today_present: int
    today_late: int
    today_absent: int
    today_on_leave: int
    pending_leave_requests: int
    monthly_payroll_total: Decimal
    department_stats: List[DepartmentStat]
    attendance_trend: List[AttendanceTrendPoint]
    payroll_trend: List[MonthlyPayrollPoint]
    recent_leaves: List[LeaveResponse]
    today_attendance: Optional[AttendanceResponse] = None
    latest_salary: Optional[SalaryResponse] = None
