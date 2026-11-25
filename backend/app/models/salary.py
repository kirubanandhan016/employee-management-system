"""Salary record model and payment status enum."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Date, Enum as SAEnum, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.user import User


class PaymentStatus(str, Enum):
    """Salary disbursement status."""

    PENDING = "pending"
    PAID = "paid"


class SalaryRecord(TimestampMixin, Base):
    """Monthly payroll record for an employee."""

    __tablename__ = "salary_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "pay_month", "pay_year", name="uq_salary_employee_period"),
        CheckConstraint("pay_month >= 1 AND pay_month <= 12", name="ck_salary_pay_month_range"),
        CheckConstraint("pay_year >= 2000 AND pay_year <= 2100", name="ck_salary_pay_year_range"),
        CheckConstraint("basic_salary >= 0", name="ck_salary_basic_non_negative"),
        CheckConstraint("allowances >= 0", name="ck_salary_allowances_non_negative"),
        CheckConstraint("deductions >= 0", name="ck_salary_deductions_non_negative"),
        CheckConstraint("net_salary >= 0", name="ck_salary_net_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pay_month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    pay_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    allowances: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(
            PaymentStatus,
            name="payment_status_enum",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    employee: Mapped["Employee"] = relationship("Employee", back_populates="salary_records")
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="created_salaries",
        foreign_keys=[created_by],
    )
