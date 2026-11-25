"""Configuration and demo-data safety tests."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, should_seed_demo_data


def test_settings_require_database_url_and_signing_key(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_reject_short_jwt_secret():
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            _env_file=None,
            DATABASE_URL="sqlite:///:memory:",
            SECRET_KEY="too-short",
        )


@pytest.mark.parametrize("environment", ["production", "prod", "test", "staging"])
def test_demo_data_is_never_seeded_outside_development(environment):
    assert should_seed_demo_data(environment, enabled=True) is False


def test_demo_data_requires_explicit_development_opt_in():
    assert should_seed_demo_data("development", enabled=False) is False
    assert should_seed_demo_data("development", enabled=True) is True
