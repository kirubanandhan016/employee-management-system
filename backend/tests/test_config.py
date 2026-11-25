"""Configuration validation tests."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_development_secret() -> None:
    with pytest.raises(ValidationError, match="explicitly configured"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="dev-insecure-secret-key-change-in-production-at-least-32-chars",
            DATABASE_URL="sqlite:///:memory:",
        )


def test_production_rejects_short_secret() -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="too-short",
            DATABASE_URL="sqlite:///:memory:",
        )


def test_production_accepts_custom_secret() -> None:
    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a-custom-production-signing-key-that-is-long-enough",
        DATABASE_URL="sqlite:///:memory:",
    )
    assert settings.SECRET_KEY == "a-custom-production-signing-key-that-is-long-enough"
