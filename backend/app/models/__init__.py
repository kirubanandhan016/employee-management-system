"""Export all SQLAlchemy models so Alembic metadata discovery sees every table."""

from app.models.attendance import Attendance, AttendanceStatus
from app.models.base import Base
from app.models.department import Department
from app.models.employee import Employee, EmployeeStatus, EmploymentType
from app.models.leave import LeaveRequest, LeaveStatus, LeaveType
from app.models.salary import PaymentStatus, SalaryRecord
from app.models.user import User, UserRole

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Department",
    "Employee",
    "EmploymentType",
    "EmployeeStatus",
    "Attendance",
    "AttendanceStatus",
    "LeaveRequest",
    "LeaveType",
    "LeaveStatus",
    "SalaryRecord",
    "PaymentStatus",
]
