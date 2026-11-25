"""Employee CRUD, search, filtering, pagination, and RBAC tests."""

from fastapi.testclient import TestClient


def test_employee_crud_and_search_pagination(client: TestClient, seed_actors: dict) -> None:
    hr_headers = seed_actors["hr_headers"]
    dept_id = seed_actors["department"].id

    # Create employee with linked user account
    create_resp = client.post(
        "/api/v1/employees",
        json={
            "first_name": "Clara",
            "last_name": "Oswald",
            "email": "clara.oswald@test.com",
            "phone": "+1-555-0999",
            "department_id": dept_id,
            "job_title": "DevOps Engineer",
            "employment_type": "full_time",
            "status": "active",
            "hire_date": "2025-01-15",
            "base_salary": "7500.00",
            "create_user_account": True,
            "account_password": "ClaraPassword123!",
            "account_role": "employee",
        },
        headers=hr_headers,
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["employee_code"].startswith("EMP-")
    assert created["user_id"] is not None
    emp_id = created["id"]

    # Search & pagination
    list_resp = client.get("/api/v1/employees?search=Clara&page=1&page_size=5", headers=hr_headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "clara.oswald@test.com"

    # Update employee
    update_resp = client.put(
        f"/api/v1/employees/{emp_id}",
        json={"job_title": "Staff DevOps Engineer", "base_salary": "8500.00"},
        headers=hr_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["job_title"] == "Staff DevOps Engineer"

    # Soft-deactivate employee
    deact_resp = client.post(f"/api/v1/employees/{emp_id}/deactivate", headers=hr_headers)
    assert deact_resp.status_code == 200
    assert deact_resp.json()["status"] == "inactive"

    # Hard delete employee
    del_resp = client.delete(f"/api/v1/employees/{emp_id}", headers=seed_actors["admin_headers"])
    assert del_resp.status_code == 200
    assert client.get(f"/api/v1/employees/{emp_id}", headers=hr_headers).status_code == 404


def test_employee_rbac_and_self_profile(client: TestClient, seed_actors: dict) -> None:
    emp1_headers = seed_actors["emp1_headers"]
    emp1_id = seed_actors["emp1"].id
    emp2_id = seed_actors["emp2"].id

    # Employee cannot list directory or view other employee
    assert client.get("/api/v1/employees", headers=emp1_headers).status_code == 403
    assert client.get(f"/api/v1/employees/{emp2_id}", headers=emp1_headers).status_code == 403
    assert client.delete(f"/api/v1/employees/{emp2_id}", headers=emp1_headers).status_code == 403

    # Employee can view own record and update own contact info
    own_resp = client.get(f"/api/v1/employees/{emp1_id}", headers=emp1_headers)
    assert own_resp.status_code == 200
    assert own_resp.json()["email"] == "emp1@test.com"

    patch_me = client.patch(
        "/api/v1/employees/me",
        json={"phone": "+1-555-7777", "address": "99 Market St"},
        headers=emp1_headers,
    )
    assert patch_me.status_code == 200
    assert patch_me.json()["phone"] == "+1-555-7777"


def test_employee_invalid_input_returns_422(client: TestClient, seed_actors: dict) -> None:
    bad_resp = client.post(
        "/api/v1/employees",
        json={
            "first_name": "Bad",
            "last_name": "Salary",
            "email": "bad@test.com",
            "job_title": "Intern",
            "hire_date": "2025-01-15",
            "base_salary": "-500.00",
        },
        headers=seed_actors["admin_headers"],
    )
    assert bad_resp.status_code == 422
