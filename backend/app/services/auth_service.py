"""Authentication and user account management services."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.employee import Employee
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, PasswordChangeRequest, RegisterRequest, TokenResponse
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate


def serialize_user(user: User) -> UserResponse:
    """Convert a User ORM instance to a safe UserResponse schema."""
    employee = user.employee
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        employee_id=employee.id if employee else None,
        employee_code=employee.employee_code if employee else None,
        department_id=employee.department_id if employee else None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def register_user(db: Session, payload: RegisterRequest) -> UserResponse:
    """Register a new user account with the standard EMPLOYEE role."""
    normalized_email = payload.email.strip().lower()
    existing = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if existing is not None:
        raise ConflictException("An account with this email already exists")

    user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Automatically link to an existing employee profile with matching email if unlinked
    matching_employee = db.scalar(
        select(Employee).where(
            func.lower(Employee.email) == normalized_email,
            Employee.user_id.is_(None),
        )
    )
    if matching_employee is not None:
        matching_employee.user_id = user.id

    db.commit()
    db.refresh(user)
    user = db.scalar(select(User).options(joinedload(User.employee)).where(User.id == user.id))
    return serialize_user(user)


def authenticate_user(db: Session, payload: LoginRequest) -> TokenResponse:
    """Verify credentials and issue a signed JWT access token."""
    normalized_email = payload.email.strip().lower()
    user = db.scalar(
        select(User)
        .options(joinedload(User.employee))
        .where(func.lower(User.email) == normalized_email)
    )
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")
    if not user.is_active:
        raise ForbiddenException("Your account has been deactivated. Contact an administrator.")

    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        extra_claims={"email": user.email},
    )
    return TokenResponse(access_token=token, user=serialize_user(user))


def change_password(db: Session, user: User, payload: PasswordChangeRequest) -> None:
    """Update the authenticated user's password after verifying current password."""
    if not verify_password(payload.current_password, user.hashed_password):
        raise BadRequestException("Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise BadRequestException("New password must be different from current password")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()


def list_users(
    db: Session,
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    page: int = 1,
    page_size: int = 10,
) -> PaginatedResponse[UserResponse]:
    """List users with optional search and role filters (Admin)."""
    stmt = select(User).options(joinedload(User.employee))
    count_stmt = select(func.count(User.id))

    if search:
        term = f"%{search.strip()}%"
        condition = or_(User.full_name.ilike(term), User.email.ilike(term))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    if role is not None:
        stmt = stmt.where(User.role == role)
        count_stmt = count_stmt.where(User.role == role)

    total = db.scalar(count_stmt) or 0
    users = db.scalars(
        stmt.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return PaginatedResponse.create(
        items=[serialize_user(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


def create_user(db: Session, payload: UserCreate) -> UserResponse:
    """Admin-only user creation supporting explicit role assignment."""
    normalized_email = payload.email.strip().lower()
    if db.scalar(select(User).where(func.lower(User.email) == normalized_email)):
        raise ConflictException("An account with this email already exists")

    user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.flush()

    matching_employee = db.scalar(
        select(Employee).where(
            func.lower(Employee.email) == normalized_email,
            Employee.user_id.is_(None),
        )
    )
    if matching_employee is not None:
        matching_employee.user_id = user.id

    db.commit()
    user = db.scalar(select(User).options(joinedload(User.employee)).where(User.id == user.id))
    return serialize_user(user)


def update_user(db: Session, user_id: int, payload: UserUpdate, current_user: User) -> UserResponse:
    """Admin-only user role/status update."""
    user = db.scalar(select(User).options(joinedload(User.employee)).where(User.id == user_id))
    if user is None:
        raise NotFoundException("User not found")

    if user.id == current_user.id and payload.is_active is False:
        raise BadRequestException("You cannot deactivate your own administrator account")
    if user.id == current_user.id and payload.role is not None and payload.role != UserRole.ADMIN:
        raise BadRequestException("You cannot demote your own administrator account")

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return serialize_user(user)
