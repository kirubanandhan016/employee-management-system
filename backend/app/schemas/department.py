"""Department CRUD and assignment schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DepartmentBase(BaseModel):
    """Shared department fields."""

    name: str = Field(..., min_length=2, max_length=120)
    code: str = Field(..., min_length=2, max_length=20)
    description: Optional[str] = Field(default=None, max_length=1000)
    manager_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class DepartmentCreate(DepartmentBase):
    """Schema to create a department."""


class DepartmentUpdate(BaseModel):
    """Schema to update an existing department."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    code: Optional[str] = Field(default=None, min_length=2, max_length=20)
    description: Optional[str] = Field(default=None, max_length=1000)
    manager_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().upper() if value is not None else None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else None


class DepartmentAssignEmployeesRequest(BaseModel):
    """Assign one or more employees to a department."""

    employee_ids: list[int] = Field(..., min_length=1)


class DepartmentResponse(BaseModel):
    """Serialized department with aggregated employee count and manager name."""

    id: int
    name: str
    code: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    employee_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
