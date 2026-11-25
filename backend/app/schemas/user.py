"""User response and administration schemas (never exposing password hashes)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserResponse(BaseModel):
    """Public-safe representation of an authenticated or managed user."""

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    employee_id: Optional[int] = None
    employee_code: Optional[str] = None
    department_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Admin-only schema for creating a user with an explicit role."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.EMPLOYEE
    is_active: bool = True


class UserUpdate(BaseModel):
    """Admin-only schema for updating a user account."""

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
