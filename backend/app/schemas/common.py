"""Shared Pydantic schemas including generic pagination responses."""

from math import ceil
from typing import Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Simple confirmation response."""

    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list envelope."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        """Construct a paginated response calculating total_pages safely."""
        total_pages = ceil(total / page_size) if total > 0 else 1
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
