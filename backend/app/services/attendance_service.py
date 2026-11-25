"""Attendance check-in, check-out, history, and reporting services."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee, EmployeeStatus
from app.models.user import User, UserRole
from app.schemas.attendance import (
    AttendanceRecordCreate,
    AttendanceReportSummary,
    AttendanceResponse,
    CheckInRequest,
    CheckOutRequest,
)
from app.schemas.common import PaginatedResponse


def serialize_attendance(att: Attendance) -> AttendanceResponse:
    """Convert Attendance ORM instance into AttendanceResponse."""
    emp = att.employee
    return AttendanceResponse(
        id=att.id,
        employee_id=att.employee_id,
        employee_name=emp.full_name if emp else None,
        employee_code=emp.employee_code if emp else None,
        department_name=emp.department.name if emp and emp.department else None,
        date=att.date,
        check_in=att.check_in,
        check_out=att.check_out,
        status=att.status,
        work_hours=att.work_hours,
        notes=att.notes,
        created_at=att.created_at,
        updated_at=att.updated_at,
    )


def _resolve_target_employee(db: Session, current_user: User, requested_employee_id: Optional[int]) -> Employee:
    if requested_employee_id is not None:
        if current_user.role == UserRole.EMPLOYEE:
            if current_user.employee is None or current_user.employee.id != requested_employee_id:
                raise ForbiddenException("Employees can only record their own attendance")
        emp = db.scalar(select(Employee).where(Employee.id == requested_employee_id))
        if emp is None:
            raise NotFoundException("Employee not found")
        return emp

    if current_user.employee is None:
        raise NotFoundException("No employee profile is linked to your account")
    return current_user.employee


def _compute_work_hours(check_in: datetime, check_out: datetime) -> Decimal:
    start = check_in if check_in.tzinfo else check_in.replace(tzinfo=timezone.utc)
    end = check_out if check_out.tzinfo else check_out.replace(tzinfo=timezone.utc)
    if end < start:
        raise BadRequestException("Check-out time cannot be earlier than check-in time")
    hours = Decimal(str((end - start).total_seconds() / 3600))
    return hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def check_in(db: Session, current_user: User, payload: CheckInRequest) -> AttendanceResponse:
    """Record daily check-in for an active employee."""
    employee = _resolve_target_employee(db, current_user, payload.employee_id)
    if employee.status != EmployeeStatus.ACTIVE:
        raise BadRequestException("Inactive or terminated employees cannot check in")

    today = date.today()
    existing = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == employee.id,
            Attendance.date == today,
        )
    )
    if existing is not None:
        raise ConflictException("Attendance for today has already been checked in")

    now = datetime.now(timezone.utc)
    record = Attendance(
        employee_id=employee.id,
        date=today,
        check_in=now,
        status=AttendanceStatus.PRESENT,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()

    refreshed = db.scalar(
        select(Attendance)
        .options(joinedload(Attendance.employee).joinedload(Employee.department))
        .where(Attendance.id == record.id)
    )
    return serialize_attendance(refreshed)


def check_out(db: Session, current_user: User, payload: CheckOutRequest) -> AttendanceResponse:
    """Record daily check-out and calculate worked hours."""
    employee = _resolve_target_employee(db, current_user, payload.employee_id)
    today = date.today()

    record = db.scalar(
        select(Attendance)
        .options(joinedload(Attendance.employee).joinedload(Employee.department))
        .where(
            Attendance.employee_id == employee.id,
            Attendance.date == today,
        )
    )
    if record is None or record.check_in is None:
        raise BadRequestException("You must check in before checking out")
    if record.check_out is not None:
        raise ConflictException("You have already checked out for today")

    now = datetime.now(timezone.utc)
    record.check_out = now
    record.work_hours = _compute_work_hours(record.check_in, now)
    if payload.notes:
        record.notes = f"{record.notes} | {payload.notes}".strip(" |") if record.notes else payload.notes

    db.commit()
    db.refresh(record)
    return serialize_attendance(record)


def upsert_manual_attendance(db: Session, payload: AttendanceRecordCreate) -> AttendanceResponse:
    """Allow Admin/HR to create or update an attendance entry for a date."""
    emp = db.scalar(select(Employee).where(Employee.id == payload.employee_id))
    if emp is None:
        raise NotFoundException("Employee not found")

    work_hours: Optional[Decimal] = None
    if payload.check_in and payload.check_out:
        work_hours = _compute_work_hours(payload.check_in, payload.check_out)

    existing = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == payload.employee_id,
            Attendance.date == payload.date,
        )
    )
    if existing is not None:
        existing.check_in = payload.check_in
        existing.check_out = payload.check_out
        existing.status = payload.status
        existing.work_hours = work_hours
        existing.notes = payload.notes
        record = existing
    else:
        record = Attendance(
            employee_id=payload.employee_id,
            date=payload.date,
            check_in=payload.check_in,
            check_out=payload.check_out,
            status=payload.status,
            work_hours=work_hours,
            notes=payload.notes,
        )
        db.add(record)

    db.commit()
    refreshed = db.scalar(
        select(Attendance)
        .options(joinedload(Attendance.employee).joinedload(Employee.department))
        .where(Attendance.id == record.id)
    )
    return serialize_attendance(refreshed)


def list_attendance(
    db: Session,
    current_user: User,
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[AttendanceStatus] = None,
    page: int = 1,
    page_size: int = 15,
) -> PaginatedResponse[AttendanceResponse]:
    """List attendance records scoped by RBAC."""
    filters = []
    if current_user.role == UserRole.EMPLOYEE:
        if current_user.employee is None:
            return PaginatedResponse.create(items=[], total=0, page=page, page_size=page_size)
        if employee_id is not None and employee_id != current_user.employee.id:
            raise ForbiddenException("You may only view your own attendance history")
        filters.append(Attendance.employee_id == current_user.employee.id)
    elif employee_id is not None:
        filters.append(Attendance.employee_id == employee_id)

    if start_date is not None:
        filters.append(Attendance.date >= start_date)
    if end_date is not None:
        filters.append(Attendance.date <= end_date)
    if status is not None:
        filters.append(Attendance.status == status)

    stmt = (
        select(Attendance)
        .options(joinedload(Attendance.employee).joinedload(Employee.department))
        .where(*filters)
    )
    count_stmt = select(func.count(Attendance.id)).where(*filters)

    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(Attendance.date.desc(), Attendance.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return PaginatedResponse.create(
        items=[serialize_attendance(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_attendance_report(
    db: Session,
    current_user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
) -> AttendanceReportSummary:
    """Generate attendance counts and average hours across a date window."""
    effective_end = end_date or date.today()
    effective_start = start_date or (effective_end - timedelta(days=29))
    if effective_end < effective_start:
        raise BadRequestException("end_date must be on or after start_date")

    filters = [Attendance.date >= effective_start, Attendance.date <= effective_end]
    stmt = select(Attendance).join(Employee, Attendance.employee_id == Employee.id)

    if current_user.role == UserRole.EMPLOYEE:
        if current_user.employee is None:
            return AttendanceReportSummary(
                start_date=effective_start,
                end_date=effective_end,
                total_records=0,
                present_count=0,
                late_count=0,
                half_day_count=0,
                absent_count=0,
                on_leave_count=0,
                average_work_hours=0.0,
            )
        filters.append(Attendance.employee_id == current_user.employee.id)
    elif department_id is not None:
        filters.append(Employee.department_id == department_id)

    records = db.scalars(stmt.where(*filters)).all()
    counts = {s: 0 for s in AttendanceStatus}
    hours_list = []
    for rec in records:
        counts[rec.status] += 1
        if rec.work_hours is not None:
            hours_list.append(float(rec.work_hours))

    avg_hours = round(sum(hours_list) / len(hours_list), 2) if hours_list else 0.0
    return AttendanceReportSummary(
        start_date=effective_start,
        end_date=effective_end,
        total_records=len(records),
        present_count=counts[AttendanceStatus.PRESENT],
        late_count=counts[AttendanceStatus.LATE],
        half_day_count=counts[AttendanceStatus.HALF_DAY],
        absent_count=counts[AttendanceStatus.ABSENT],
        on_leave_count=counts[AttendanceStatus.ON_LEAVE],
        average_work_hours=avg_hours,
    )
