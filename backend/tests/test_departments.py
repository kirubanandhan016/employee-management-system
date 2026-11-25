"""Department CRUD, safe deletion, employee assignment, and RBAC tests."""

from fastapi.testclient import TestClient


def test_department_crud_and_safe_delete(client: TestClient, seed_actors: dict) -> None:
    admin_headers = seed_actors["admin_headers"]
    emp1_headers = seed_actors["emp1_headers"]
    existing_dept_id = seed_actors["department"].id
    emp2_id = seed_actors["emp2"].id

    # Employee cannot create or delete departments
    assert (
        client.post(
            "/api/v1/departments",
            json={"name": "Marketing", "code": "MKT"},
            headers=emp1_headers,
        ).status_code
        == 403
    )

    # Deleting department with assigned employees must fail with 409 Conflict
    blocked_del = client.delete(f"/api/v1/departments/{existing_dept_id}", headers=admin_headers)
    assert blocked_del.status_code == 409

    # Create a new department
    create_resp = client.post(
        "/api/v1/departments",
        json={"name": "Quality Assurance", "code": "qa", "description": "Testing & release quality"},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    new_dept = create_resp.json()
    assert new_dept["code"] == "QA"
    new_dept_id = new_dept["id"]

    # Update department
    upd_resp = client.put(
        f"/api/v1/departments/{new_dept_id}",
        json={"description": "Automated and manual QA"},
        headers=admin_headers,
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["description"] == "Automated and manual QA"

    # Assign employee to new department
    assign_resp = client.post(
        f"/api/v1/departments/{new_dept_id}/assign-employees",
        json={"employee_ids": [emp2_id]},
        headers=admin_headers,
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["employee_count"] == 1

    # Reassign back so QA becomes empty, then delete succeeds
    client.post(
        f"/api/v1/departments/{existing_dept_id}/assign-employees",
        json={"employee_ids": [emp2_id]},
        headers=admin_headers,
    )
    del_resp = client.delete(f"/api/v1/departments/{new_dept_id}", headers=admin_headers)
    assert del_resp.status_code == 200
