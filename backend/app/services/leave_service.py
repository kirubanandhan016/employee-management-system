"""Leave application, cancellation, and approval workflow services."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models.employee import Employee
from app.models.leave import LeaveRequest, LeaveStatus, LeaveType
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.leave import LeaveCreate, LeaveResponse, LeaveReviewRequest


def serialize_leave(leave: LeaveRequest) -> LeaveResponse:
    """Convert LeaveRequest ORM row into LeaveResponse."""
    emp = leave.employee
    reviewer = leave.reviewer
    return LeaveResponse(
        id=leave.id,
        employee_id=leave.employee_id,
        employee_name=emp.full_name if emp else None,
        employee_code=emp.employee_code if emp else None,
        department_name=emp.department.name if emp and emp.department else None,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        days_count=leave.days_count,
        reason=leave.reason,
        status=leave.status,
        reviewed_by=leave.reviewed_by,
        reviewer_name=reviewer.full_name if reviewer else None,
        reviewed_at=leave.reviewed_at,
        review_comment=leave.review_comment,
        created_at=leave.created_at,
        updated_at=leave.updated_at,
    )


def apply_leave(db: Session, current_user: User, payload: LeaveCreate) -> LeaveResponse:
    """Submit a new leave request after checking for overlapping dates."""
    if payload.employee_id is not None:
        if current_user.role == UserRole.EMPLOYEE:
            if current_user.employee is None or current_user.employee.id != payload.employee_id:
                raise ForbiddenException("Employees can only apply for leave on their own behalf")
        emp = db.scalar(select(Employee).where(Employee.id == payload.employee_id))
        if emp is None:
            raise NotFoundException("Employee not found")
        target_employee_id = emp.id
    else:
        if current_user.employee is None:
            raise NotFoundException("No employee profile is linked to your user account")
        target_employee_id = current_user.employee.id

    overlap = db.scalar(
        select(LeaveRequest.id).where(
            LeaveRequest.employee_id == target_employee_id,
            LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
            LeaveRequest.start_date <= payload.end_date,
            LeaveRequest.end_date >= payload.start_date,
        )
    )
    if overlap is not None:
        raise ConflictException("An overlapping pending or approved leave request already exists for these dates")

    days_count = (payload.end_date - payload.start_date).days + 1
    leave = LeaveRequest(
        employee_id=target_employee_id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        days_count=days_count,
        reason=payload.reason.strip(),
        status=LeaveStatus.PENDING,
    )
    db.add(leave)
    db.commit()

    created = db.scalar(
        select(LeaveRequest)
        .options(
            joinedload(LeaveRequest.employee).joinedload(Employee.department),
            joinedload(LeaveRequest.reviewer),
        )
        .where(LeaveRequest.id == leave.id)
    )
    return serialize_leave(created)


def list_leaves(
    db: Session,
    current_user: User,
    employee_id: Optional[int] = None,
    status: Optional[LeaveStatus] = None,
    leave_type: Optional[LeaveType] = None,
    page: int = 1,
    page_size: int = 15,
) -> PaginatedResponse[LeaveResponse]:
    """List leave requests with RBAC filtering and pagination."""
    filters = []
    if current_user.role == UserRole.EMPLOYEE:
        if current_user.employee is None:
            return PaginatedResponse.create(items=[], total=0, page=page, page_size=page_size)
        if employee_id is not None and employee_id != current_user.employee.id:
            raise ForbiddenException("You may only view your own leave requests")
        filters.append(LeaveRequest.employee_id == current_user.employee.id)
    elif employee_id is not None:
        filters.append(LeaveRequest.employee_id == employee_id)

    if status is not None:
        filters.append(LeaveRequest.status == status)
    if leave_type is not None:
        filters.append(LeaveRequest.leave_type == leave_type)

    stmt = (
        select(LeaveRequest)
        .options(
            joinedload(LeaveRequest.employee).joinedload(Employee.department),
            joinedload(LeaveRequest.reviewer),
        )
        .where(*filters)
    )
    count_stmt = select(func.count(LeaveRequest.id)).where(*filters)

    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(LeaveRequest.created_at.desc(), LeaveRequest.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return PaginatedResponse.create(
        items=[serialize_leave(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def review_leave(
    db: Session,
    leave_id: int,
    reviewer: User,
    payload: LeaveReviewRequest,
) -> LeaveResponse:
    """Approve or reject a pending leave request (Admin / HR Manager)."""
    leave = db.scalar(
        select(LeaveRequest)
        .options(
            joinedload(LeaveRequest.employee).joinedload(Employee.department),
            joinedload(LeaveRequest.reviewer),
        )
        .where(LeaveRequest.id == leave_id)
    )
    if leave is None:
        raise NotFoundException("Leave request not found")
    if leave.status != LeaveStatus.PENDING:
        raise ConflictException(f"Leave request has already been {leave.status.value}")

    leave.status = LeaveStatus.APPROVED if payload.status == "approved" else LeaveStatus.REJECTED
    leave.reviewed_by = reviewer.id
    leave.reviewed_at = datetime.now(timezone.utc)
    leave.review_comment = payload.review_comment.strip() if payload.review_comment else None

    db.commit()
    refreshed = db.scalar(
        select(LeaveRequest)
        .options(
            joinedload(LeaveRequest.employee).joinedload(Employee.department),
            joinedload(LeaveRequest.reviewer),
        )
        .where(LeaveRequest.id == leave_id)
    )
    return serialize_leave(refreshed)


def cancel_leave(db: Session, leave_id: int, current_user: User) -> LeaveResponse:
    """Cancel a pending leave request."""
    leave = db.scalar(
        select(LeaveRequest)
        .options(
            joinedload(LeaveRequest.employee).joinedload(Employee.department),
            joinedload(LeaveRequest.reviewer),
        )
        .where(LeaveRequest.id == leave_id)
    )
    if leave is None:
        raise NotFoundException("Leave request not found")

    if current_user.role == UserRole.EMPLOYEE:
        if current_user.employee is None or leave.employee_id != current_user.employee.id:
            raise ForbiddenException("You may only cancel your own leave requests")

    if leave.status != LeaveStatus.PENDING:
        raise BadRequestException("Only pending leave requests can be cancelled")

    leave.status = LeaveStatus.CANCELLED
    db.commit()
    db.refresh(leave)
    return serialize_leave(leave)
