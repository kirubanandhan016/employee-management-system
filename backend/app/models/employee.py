"""Employee profile model and employment enums."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, Date, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance import Attendance
    from app.models.department import Department
    from app.models.leave import LeaveRequest
    from app.models.salary import SalaryRecord
    from app.models.user import User


class EmploymentType(str, Enum):
    """Employment contract classification."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"


class EmployeeStatus(str, Enum):
    """Current employment status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"


class Employee(TimestampMixin, Base):
    """Company employee record linked optionally to a User login account."""

    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("base_salary >= 0", name="ck_employees_base_salary_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
        index=True,
    )
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_title: Mapped[str] = mapped_column(String(120), nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(
        SAEnum(
            EmploymentType,
            name="employment_type_enum",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=EmploymentType.FULL_TIME,
        nullable=False,
    )
    status: Mapped[EmployeeStatus] = mapped_column(
        SAEnum(
            EmployeeStatus,
            name="employee_status_enum",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=EmployeeStatus.ACTIVE,
        index=True,
        nullable=False,
    )
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    base_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="employee")
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="employees",
        foreign_keys=[department_id],
    )
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    leave_requests: Mapped[List["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    salary_records: Mapped[List["SalaryRecord"]] = relationship(
        "SalaryRecord",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        """Return formatted full name."""
        return f"{self.first_name} {self.last_name}".strip()
