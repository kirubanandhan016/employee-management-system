"""Leave application, overlap validation, cancellation, and HR/Admin approval tests."""

from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_leave_application_and_approval_workflow(client: TestClient, seed_actors: dict) -> None:
    emp1_headers = seed_actors["emp1_headers"]
    emp2_headers = seed_actors["emp2_headers"]
    hr_headers = seed_actors["hr_headers"]

    start = date.today() + timedelta(days=5)
    end = start + timedelta(days=2)

    # Invalid date range fails validation
    bad_dates = client.post(
        "/api/v1/leaves",
        json={
            "leave_type": "annual",
            "start_date": end.isoformat(),
            "end_date": start.isoformat(),
            "reason": "Backwards dates test",
        },
        headers=emp1_headers,
    )
    assert bad_dates.status_code == 422

    # Valid leave application
    apply_resp = client.post(
        "/api/v1/leaves",
        json={
            "leave_type": "annual",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "reason": "Scheduled family vacation",
        },
        headers=emp1_headers,
    )
    assert apply_resp.status_code == 201
    leave = apply_resp.json()
    assert leave["days_count"] == 3
    assert leave["status"] == "pending"
    leave_id = leave["id"]

    # Overlapping leave blocked
    overlap_resp = client.post(
        "/api/v1/leaves",
        json={
            "leave_type": "casual",
            "start_date": (start + timedelta(days=1)).isoformat(),
            "end_date": (end + timedelta(days=1)).isoformat(),
            "reason": "Overlapping request",
        },
        headers=emp1_headers,
    )
    assert overlap_resp.status_code == 409

    # Employee cannot approve leave
    emp_approve = client.patch(
        f"/api/v1/leaves/{leave_id}/review",
        json={"status": "approved"},
        headers=emp1_headers,
    )
    assert emp_approve.status_code == 403

    # Another employee cannot cancel employee 1's leave
    other_cancel = client.post(f"/api/v1/leaves/{leave_id}/cancel", headers=emp2_headers)
    assert other_cancel.status_code == 403

    # HR Manager approves leave
    hr_approve = client.patch(
        f"/api/v1/leaves/{leave_id}/review",
        json={"status": "approved", "review_comment": "Approved by HR"},
        headers=hr_headers,
    )
    assert hr_approve.status_code == 200
    assert hr_approve.json()["status"] == "approved"
    assert hr_approve.json()["reviewer_name"] == "HR Manager"

    # Re-reviewing an already approved leave is blocked
    re_review = client.patch(
        f"/api/v1/leaves/{leave_id}/review",
        json={"status": "rejected"},
        headers=hr_headers,
    )
    assert re_review.status_code == 409
