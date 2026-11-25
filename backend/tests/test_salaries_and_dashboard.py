"""Salary calculation, strict privacy RBAC, and dashboard analytics tests."""

from fastapi.testclient import TestClient


def test_salary_crud_calculation_and_privacy_rbac(client: TestClient, seed_actors: dict) -> None:
    admin_headers = seed_actors["admin_headers"]
    hr_headers = seed_actors["hr_headers"]
    emp1_headers = seed_actors["emp1_headers"]
    emp1_id = seed_actors["emp1"].id
    emp2_id = seed_actors["emp2"].id

    # Employee cannot create salary records
    emp_create = client.post(
        "/api/v1/salaries",
        json={
            "employee_id": emp1_id,
            "pay_month": 11,
            "pay_year": 2026,
            "basic_salary": "6000.00",
            "allowances": "500.00",
            "deductions": "300.00",
        },
        headers=emp1_headers,
    )
    assert emp_create.status_code == 403

    # Deductions > gross fails validation
    bad_sal = client.post(
        "/api/v1/salaries",
        json={
            "employee_id": emp1_id,
            "pay_month": 11,
            "pay_year": 2026,
            "basic_salary": "1000.00",
            "allowances": "100.00",
            "deductions": "1500.00",
        },
        headers=admin_headers,
    )
    assert bad_sal.status_code == 422

    # Admin creates salary records for emp1 and emp2
    sal1 = client.post(
        "/api/v1/salaries",
        json={
            "employee_id": emp1_id,
            "pay_month": 11,
            "pay_year": 2026,
            "basic_salary": "6000.00",
            "allowances": "750.00",
            "deductions": "450.00",
            "payment_status": "paid",
        },
        headers=admin_headers,
    )
    assert sal1.status_code == 201
    assert sal1.json()["net_salary"] == "6300.00"
    sal1_id = sal1.json()["id"]

    sal2 = client.post(
        "/api/v1/salaries",
        json={
            "employee_id": emp2_id,
            "pay_month": 11,
            "pay_year": 2026,
            "basic_salary": "5200.00",
            "allowances": "300.00",
            "deductions": "200.00",
        },
        headers=hr_headers,
    )
    assert sal2.status_code == 201

    # Duplicate month/year for same employee blocked
    dup_sal = client.post(
        "/api/v1/salaries",
        json={
            "employee_id": emp1_id,
            "pay_month": 11,
            "pay_year": 2026,
            "basic_salary": "6000.00",
        },
        headers=admin_headers,
    )
    assert dup_sal.status_code == 409

    # Employee 1 sees only their own salary record and cannot query Employee 2's salary
    own_sals = client.get("/api/v1/salaries", headers=emp1_headers)
    assert own_sals.status_code == 200
    assert own_sals.json()["total"] == 1
    assert own_sals.json()["items"][0]["employee_id"] == emp1_id

    forbidden_sal = client.get(f"/api/v1/salaries?employee_id={emp2_id}", headers=emp1_headers)
    assert forbidden_sal.status_code == 403

    # Only Admin can delete salary record (HR gets 403)
    assert client.delete(f"/api/v1/salaries/{sal1_id}", headers=hr_headers).status_code == 403
    assert client.delete(f"/api/v1/salaries/{sal1_id}", headers=admin_headers).status_code == 200


def test_dashboard_overview_role_scoping(client: TestClient, seed_actors: dict) -> None:
    admin_dash = client.get("/api/v1/dashboard/overview", headers=seed_actors["admin_headers"])
    assert admin_dash.status_code == 200
    admin_data = admin_dash.json()
    assert admin_data["total_employees"] == 2
    assert admin_data["total_departments"] == 1
    assert len(admin_data["department_stats"]) == 1

    emp_dash = client.get("/api/v1/dashboard/overview", headers=seed_actors["emp1_headers"])
    assert emp_dash.status_code == 200
    emp_data = emp_dash.json()
    assert emp_data["role"] == "employee"
    assert emp_data["department_stats"] == []
