"""Attendance check-in, check-out, history, report, and RBAC tests."""

from fastapi.testclient import TestClient


def test_check_in_check_out_and_duplicate_protection(client: TestClient, seed_actors: dict) -> None:
    emp1_headers = seed_actors["emp1_headers"]

    # Cannot check out before checking in
    premature_out = client.post("/api/v1/attendance/check-out", json={}, headers=emp1_headers)
    assert premature_out.status_code == 400

    # Check in
    in_resp = client.post(
        "/api/v1/attendance/check-in",
        json={"notes": "Starting shift"},
        headers=emp1_headers,
    )
    assert in_resp.status_code == 201
    assert in_resp.json()["status"] == "present"
    assert in_resp.json()["check_in"] is not None

    # Duplicate check-in blocked
    dup_in = client.post("/api/v1/attendance/check-in", json={}, headers=emp1_headers)
    assert dup_in.status_code == 409

    # Check out computes work_hours
    out_resp = client.post("/api/v1/attendance/check-out", json={}, headers=emp1_headers)
    assert out_resp.status_code == 200
    assert out_resp.json()["check_out"] is not None
    assert float(out_resp.json()["work_hours"]) >= 0.0

    # Duplicate check-out blocked
    dup_out = client.post("/api/v1/attendance/check-out", json={}, headers=emp1_headers)
    assert dup_out.status_code == 409


def test_attendance_scoping_and_reports(client: TestClient, seed_actors: dict) -> None:
    emp1_headers = seed_actors["emp1_headers"]
    emp2_headers = seed_actors["emp2_headers"]
    hr_headers = seed_actors["hr_headers"]

    client.post("/api/v1/attendance/check-in", json={}, headers=emp1_headers)
    client.post("/api/v1/attendance/check-in", json={}, headers=emp2_headers)

    # Employee 1 cannot query Employee 2's attendance
    forbidden = client.get(
        f"/api/v1/attendance?employee_id={seed_actors['emp2'].id}",
        headers=emp1_headers,
    )
    assert forbidden.status_code == 403

    # Employee 1 sees only own 1 record
    own_list = client.get("/api/v1/attendance", headers=emp1_headers)
    assert own_list.status_code == 200
    assert own_list.json()["total"] == 1

    # HR sees both records and company report
    hr_list = client.get("/api/v1/attendance", headers=hr_headers)
    assert hr_list.status_code == 200
    assert hr_list.json()["total"] == 2

    report = client.get("/api/v1/attendance/report", headers=hr_headers)
    assert report.status_code == 200
    assert report.json()["present_count"] == 2
