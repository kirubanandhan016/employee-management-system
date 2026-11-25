"""Salary record management and payroll calculation services."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models.employee import Employee
from app.models.salary import PaymentStatus, SalaryRecord
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.salary import SalaryCreate, SalaryResponse, SalarySummaryResponse, SalaryUpdate


def serialize_salary(sal: SalaryRecord) -> SalaryResponse:
    """Convert SalaryRecord ORM instance into SalaryResponse."""
    emp = sal.employee
    return SalaryResponse(
        id=sal.id,
        employee_id=sal.employee_id,
        employee_name=emp.full_name if emp else None,
        employee_code=emp.employee_code if emp else None,
        department_name=emp.department.name if emp and emp.department else None,
        pay_month=sal.pay_month,
        pay_year=sal.pay_year,
        basic_salary=sal.basic_salary,
        allowances=sal.allowances,
        deductions=sal.deductions,
        net_salary=sal.net_salary,
        payment_status=sal.payment_status,
        payment_date=sal.payment_date,
        notes=sal.notes,
        created_by=sal.created_by,
        created_at=sal.created_at,
        updated_at=sal.updated_at,
    )


def _compute_net_salary(basic: Decimal, allowances: Decimal, deductions: Decimal) -> Decimal:
    net = basic + allowances - deductions
    if net < Decimal("0.00"):
        raise BadRequestException("Deductions cannot exceed basic salary plus allowances")
    return net


def create_salary_record(db: Session, current_user: User, payload: SalaryCreate) -> SalaryResponse:
    """Create a monthly salary record computing net_salary server-side."""
    emp = db.scalar(select(Employee).where(Employee.id == payload.employee_id))
    if emp is None:
        raise NotFoundException("Employee not found")

    duplicate = db.scalar(
        select(SalaryRecord.id).where(
            SalaryRecord.employee_id == payload.employee_id,
            SalaryRecord.pay_month == payload.pay_month,
            SalaryRecord.pay_year == payload.pay_year,
        )
    )
    if duplicate is not None:
        raise ConflictException(
            f"Salary record for {payload.pay_month:02d}/{payload.pay_year} already exists for this employee"
        )

    net_salary = _compute_net_salary(payload.basic_salary, payload.allowances, payload.deductions)
    payment_date = payload.payment_date
    if payload.payment_status == PaymentStatus.PAID and payment_date is None:
        payment_date = date.today()

    record = SalaryRecord(
        employee_id=payload.employee_id,
        pay_month=payload.pay_month,
        pay_year=payload.pay_year,
        basic_salary=payload.basic_salary,
        allowances=payload.allowances,
        deductions=payload.deductions,
        net_salary=net_salary,
        payment_status=payload.payment_status,
        payment_date=payment_date,
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(record)
    db.commit()

    created = db.scalar(
        select(SalaryRecord)
        .options(joinedload(SalaryRecord.employee).joinedload(Employee.department))
        .where(SalaryRecord.id == record.id)
    )
    return serialize_salary(created)


def update_salary_record(db: Session, salary_id: int, payload: SalaryUpdate) -> SalaryResponse:
    """Update a salary record and recalculate net_salary."""
    record = db.scalar(
        select(SalaryRecord)
        .options(joinedload(SalaryRecord.employee).joinedload(Employee.department))
        .where(SalaryRecord.id == salary_id)
    )
    if record is None:
        raise NotFoundException("Salary record not found")

    if payload.basic_salary is not None:
        record.basic_salary = payload.basic_salary
    if payload.allowances is not None:
        record.allowances = payload.allowances
    if payload.deductions is not None:
        record.deductions = payload.deductions

    record.net_salary = _compute_net_salary(record.basic_salary, record.allowances, record.deductions)

    if payload.payment_status is not None:
        record.payment_status = payload.payment_status
        if payload.payment_status == PaymentStatus.PAID and record.payment_date is None and payload.payment_date is None:
            record.payment_date = date.today()
    if "payment_date" in payload.model_fields_set:
        record.payment_date = payload.payment_date
    if "notes" in payload.model_fields_set:
        record.notes = payload.notes

    db.commit()
    db.refresh(record)
    return serialize_salary(record)


def delete_salary_record(db: Session, salary_id: int) -> None:
    """Delete a salary record (Admin only)."""
    record = db.scalar(select(SalaryRecord).where(SalaryRecord.id == salary_id))
    if record is None:
        raise NotFoundException("Salary record not found")
    db.delete(record)
    db.commit()


def list_salaries(
    db: Session,
    current_user: User,
    employee_id: Optional[int] = None,
    pay_month: Optional[int] = None,
    pay_year: Optional[int] = None,
    payment_status: Optional[PaymentStatus] = None,
    page: int = 1,
    page_size: int = 15,
) -> PaginatedResponse[SalaryResponse]:
    """List salary records enforcing strict employee isolation."""
    filters = []
    if current_user.role == UserRole.EMPLOYEE:
        if current_user.employee is None:
            return PaginatedResponse.create(items=[], total=0, page=page, page_size=page_size)
        if employee_id is not None and employee_id != current_user.employee.id:
            raise ForbiddenException("You may only view your own salary records")
        filters.append(SalaryRecord.employee_id == current_user.employee.id)
    elif employee_id is not None:
        filters.append(SalaryRecord.employee_id == employee_id)

    if pay_month is not None:
        filters.append(SalaryRecord.pay_month == pay_month)
    if pay_year is not None:
        filters.append(SalaryRecord.pay_year == pay_year)
    if payment_status is not None:
        filters.append(SalaryRecord.payment_status == payment_status)

    stmt = (
        select(SalaryRecord)
        .options(joinedload(SalaryRecord.employee).joinedload(Employee.department))
        .where(*filters)
    )
    count_stmt = select(func.count(SalaryRecord.id)).where(*filters)

    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(SalaryRecord.pay_year.desc(), SalaryRecord.pay_month.desc(), SalaryRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return PaginatedResponse.create(
        items=[serialize_salary(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_salary_summary(
    db: Session,
    current_user: User,
    pay_month: Optional[int] = None,
    pay_year: Optional[int] = None,
) -> SalarySummaryResponse:
    """Compute aggregated payroll totals."""
    filters = []
    if current_user.role == UserRole.EMPLOYEE:
        if current_user.employee is None:
            return SalarySummaryResponse(
                total_records=0,
                total_basic_salary=Decimal("0.00"),
                total_allowances=Decimal("0.00"),
                total_deductions=Decimal("0.00"),
                total_net_payroll=Decimal("0.00"),
                paid_count=0,
                pending_count=0,
            )
        filters.append(SalaryRecord.employee_id == current_user.employee.id)

    if pay_month is not None:
        filters.append(SalaryRecord.pay_month == pay_month)
    if pay_year is not None:
        filters.append(SalaryRecord.pay_year == pay_year)

    records = db.scalars(select(SalaryRecord).where(*filters)).all()
    total_basic = sum((r.basic_salary for r in records), Decimal("0.00"))
    total_allowances = sum((r.allowances for r in records), Decimal("0.00"))
    total_deductions = sum((r.deductions for r in records), Decimal("0.00"))
    total_net = sum((r.net_salary for r in records), Decimal("0.00"))
    paid_count = sum(1 for r in records if r.payment_status == PaymentStatus.PAID)
    pending_count = sum(1 for r in records if r.payment_status == PaymentStatus.PENDING)

    return SalarySummaryResponse(
        total_records=len(records),
        total_basic_salary=total_basic,
        total_allowances=total_allowances,
        total_deductions=total_deductions,
        total_net_payroll=total_net,
        paid_count=paid_count,
        pending_count=pending_count,
    )
