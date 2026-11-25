"""Authentication and role-based access control (RBAC) dependencies."""

from typing import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db
from app.models.employee import Employee
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate Bearer JWT token and return the authenticated active User."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("Missing or invalid authorization token")

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        if subject is None:
            raise UnauthorizedException("Invalid token payload")
        user_id = int(subject)
    except (jwt.PyJWTError, ValueError) as exc:
        raise UnauthorizedException("Invalid or expired token") from exc

    user = db.scalar(
        select(User)
        .options(joinedload(User.employee))
        .where(User.id == user_id)
    )
    if user is None:
        raise UnauthorizedException("User account no longer exists")
    if not user.is_active:
        raise ForbiddenException("User account is deactivated")

    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    """Return a dependency enforcing that the current user holds one of the allowed roles."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException("You do not have permission to perform this action")
        return current_user

    return role_checker


def get_current_employee(current_user: User = Depends(get_current_user)) -> Employee:
    """Return the Employee profile linked to the authenticated user."""
    if current_user.employee is None:
        raise NotFoundException("No employee profile is linked to this user account")
    return current_user.employee
