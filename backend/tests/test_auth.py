"""Authentication, JWT, password hashing, and user administration tests."""

from fastapi.testclient import TestClient


def test_register_and_login_flow(client: TestClient) -> None:
    register_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.hire@company.com",
            "full_name": "New Hire",
            "password": "StrongPassword123!",
        },
    )
    assert register_resp.status_code == 201
    user_data = register_resp.json()
    assert user_data["email"] == "new.hire@company.com"
    assert user_data["role"] == "employee"
    assert "hashed_password" not in user_data

    # Duplicate email fails with 409
    dup_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "NEW.HIRE@company.com",
            "full_name": "Duplicate Hire",
            "password": "StrongPassword123!",
        },
    )
    assert dup_resp.status_code == 409

    # Login succeeds and returns JWT
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "new.hire@company.com", "password": "StrongPassword123!"},
    )
    assert login_resp.status_code == 200
    token_payload = login_resp.json()
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]
    assert "hashed_password" not in token_payload["user"]

    # Me endpoint works with bearer token
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "new.hire@company.com"


def test_invalid_login_and_unauthenticated_requests(client: TestClient, seed_actors: dict) -> None:
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "WrongPassword"},
    )
    assert bad_login.status_code == 401

    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"}).status_code == 401


def test_change_password_and_logout(client: TestClient, seed_actors: dict) -> None:
    headers = seed_actors["emp1_headers"]

    wrong_change = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongPassword", "new_password": "NewStrongPassword1"},
        headers=headers,
    )
    assert wrong_change.status_code == 400

    ok_change = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "EmpPass@123", "new_password": "NewStrongPassword1"},
        headers=headers,
    )
    assert ok_change.status_code == 200

    relogin = client.post(
        "/api/v1/auth/login",
        json={"email": "emp1@test.com", "password": "NewStrongPassword1"},
    )
    assert relogin.status_code == 200

    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200


def test_user_management_admin_only_rbac(client: TestClient, seed_actors: dict) -> None:
    assert client.get("/api/v1/users", headers=seed_actors["emp1_headers"]).status_code == 403
    assert client.get("/api/v1/users", headers=seed_actors["hr_headers"]).status_code == 403

    create_resp = client.post(
        "/api/v1/users",
        json={
            "email": "second.hr@test.com",
            "full_name": "Second HR",
            "password": "Password123!",
            "role": "hr_manager",
        },
        headers=seed_actors["admin_headers"],
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["role"] == "hr_manager"

    list_resp = client.get("/api/v1/users", headers=seed_actors["admin_headers"])
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 5
