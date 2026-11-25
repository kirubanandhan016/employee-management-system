"""Role-aware dashboard analytics and KPI aggregation service."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance, AttendanceStatus
from app.models.department import Department
from app.models.employee import Employee, EmployeeStatus
from app.models.leave import LeaveRequest, LeaveStatus
from app.models.salary import PaymentStatus, SalaryRecord
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    AttendanceTrendPoint,
    DashboardOverviewResponse,
    DepartmentStat,
    MonthlyPayrollPoint,
)
from app.services.attendance_service import serialize_attendance
from app.services.leave_service import serialize_leave
from app.services.salary_service import serialize_salary


def get_dashboard_overview(db: Session, current_user: User) -> DashboardOverviewResponse:
    """Compute real-time analytics overview scoped to the caller's role."""
    today = date.today()
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR_MANAGER)
    own_employee = current_user.employee

    today_att_row = None
    latest_salary_row = None
    if own_employee is not None:
        today_att_row = db.scalar(
            select(Attendance)
            .options(joinedload(Attendance.employee).joinedload(Employee.department))
            .where(Attendance.employee_id == own_employee.id, Attendance.date == today)
        )
        latest_salary_row = db.scalar(
            select(SalaryRecord)
            .options(joinedload(SalaryRecord.employee).joinedload(Employee.department))
            .where(SalaryRecord.employee_id == own_employee.id)
            .order_by(SalaryRecord.pay_year.desc(), SalaryRecord.pay_month.desc())
            .limit(1)
        )

    if not is_privileged:
        # Strict privacy: employees only receive personal KPIs and trends
        emp_id = own_employee.id if own_employee else -1
        pending_leaves = (
            db.scalar(
                select(func.count(LeaveRequest.id)).where(
                    LeaveRequest.employee_id == emp_id,
                    LeaveRequest.status == LeaveStatus.PENDING,
                )
            )
            or 0
        )
        recent_leave_rows = db.scalars(
            select(LeaveRequest)
            .options(
                joinedload(LeaveRequest.employee).joinedload(Employee.department),
                joinedload(LeaveRequest.reviewer),
            )
            .where(LeaveRequest.employee_id == emp_id)
            .order_by(LeaveRequest.created_at.desc())
            .limit(5)
        ).all()

        personal_salaries = db.scalars(
            select(SalaryRecord)
            .where(SalaryRecord.employee_id == emp_id)
            .order_by(SalaryRecord.pay_year.desc(), SalaryRecord.pay_month.desc())
            .limit(6)
        ).all()

        payroll_trend = [
            MonthlyPayrollPoint(
                period=f"{rec.pay_year}-{rec.pay_month:02d}",
                total_net_salary=rec.net_salary,
                paid_amount=rec.net_salary if rec.payment_status == PaymentStatus.PAID else Decimal("0.00"),
                record_count=1,
            )
            for rec in reversed(personal_salaries)
        ]

        start_7d = today - timedelta(days=6)
        own_att_rows = db.scalars(
            select(Attendance).where(
                Attendance.employee_id == emp_id,
                Attendance.date >= start_7d,
                Attendance.date <= today,
            )
        ).all()
        att_by_date = {r.date: r for r in own_att_rows}
        attendance_trend = []
        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            rec = att_by_date.get(day)
            attendance_trend.append(
                AttendanceTrendPoint(
                    date=day.isoformat(),
                    present=1 if rec and rec.status == AttendanceStatus.PRESENT else 0,
                    late=1 if rec and rec.status == AttendanceStatus.LATE else 0,
                    absent=1 if rec and rec.status == AttendanceStatus.ABSENT else 0,
                    on_leave=1 if rec and rec.status == AttendanceStatus.ON_LEAVE else 0,
                )
            )

        return DashboardOverviewResponse(
            role=current_user.role.value,
            total_employees=1 if own_employee else 0,
            active_employees=1 if own_employee and own_employee.status == EmployeeStatus.ACTIVE else 0,
            inactive_employees=1 if own_employee and own_employee.status != EmployeeStatus.ACTIVE else 0,
            total_departments=1 if own_employee and own_employee.department_id else 0,
            today_present=1 if today_att_row and today_att_row.status == AttendanceStatus.PRESENT else 0,
            today_late=1 if today_att_row and today_att_row.status == AttendanceStatus.LATE else 0,
            today_absent=1 if today_att_row and today_att_row.status == AttendanceStatus.ABSENT else 0,
            today_on_leave=1 if today_att_row and today_att_row.status == AttendanceStatus.ON_LEAVE else 0,
            pending_leave_requests=pending_leaves,
            monthly_payroll_total=latest_salary_row.net_salary if latest_salary_row else Decimal("0.00"),
            department_stats=[],
            attendance_trend=attendance_trend,
            payroll_trend=payroll_trend,
            recent_leaves=[serialize_leave(l) for l in recent_leave_rows],
            today_attendance=serialize_attendance(today_att_row) if today_att_row else None,
            latest_salary=serialize_salary(latest_salary_row) if latest_salary_row else None,
        )

    # Admin & HR Manager company-wide aggregations
    total_employees = db.scalar(select(func.count(Employee.id))) or 0
    active_employees = (
        db.scalar(select(func.count(Employee.id)).where(Employee.status == EmployeeStatus.ACTIVE)) or 0
    )
    inactive_employees = total_employees - active_employees
    total_departments = db.scalar(select(func.count(Department.id))) or 0

    today_rows = db.scalars(select(Attendance).where(Attendance.date == today)).all()
    today_present = sum(1 for r in today_rows if r.status == AttendanceStatus.PRESENT)
    today_late = sum(1 for r in today_rows if r.status == AttendanceStatus.LATE)
    today_absent = sum(1 for r in today_rows if r.status == AttendanceStatus.ABSENT)
    today_on_leave = sum(1 for r in today_rows if r.status == AttendanceStatus.ON_LEAVE)

    pending_leaves = (
        db.scalar(select(func.count(LeaveRequest.id)).where(LeaveRequest.status == LeaveStatus.PENDING)) or 0
    )

    # Department breakdown
    dept_rows = db.execute(
        select(
            Department.id,
            Department.name,
            Department.code,
            func.count(Employee.id),
            func.coalesce(func.sum(Employee.base_salary), 0),
        )
        .outerjoin(Employee, Employee.department_id == Department.id)
        .group_by(Department.id, Department.name, Department.code)
        .order_by(func.count(Employee.id).desc(), Department.name.asc())
    ).all()

    department_stats = [
        DepartmentStat(
            department_id=dept_id,
            department_name=dept_name,
            department_code=dept_code,
            employee_count=emp_count,
            total_base_salary=Decimal(str(salary_sum)),
        )
        for dept_id, dept_name, dept_code, emp_count, salary_sum in dept_rows
    ]

    # 7-day attendance trend
    start_7d = today - timedelta(days=6)
    att_7d = db.scalars(
        select(Attendance).where(Attendance.date >= start_7d, Attendance.date <= today)
    ).all()
    grouped_att: dict[date, list[Attendance]] = {}
    for row in att_7d:
        grouped_att.setdefault(row.date, []).append(row)

    attendance_trend = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_rows = grouped_att.get(day, [])
        attendance_trend.append(
            AttendanceTrendPoint(
                date=day.isoformat(),
                present=sum(1 for r in day_rows if r.status == AttendanceStatus.PRESENT),
                late=sum(1 for r in day_rows if r.status == AttendanceStatus.LATE),
                absent=sum(1 for r in day_rows if r.status == AttendanceStatus.ABSENT),
                on_leave=sum(1 for r in day_rows if r.status == AttendanceStatus.ON_LEAVE),
            )
        )

    # Payroll trend (up to 6 most recent periods)
    salary_rows = db.scalars(
        select(SalaryRecord).order_by(SalaryRecord.pay_year.desc(), SalaryRecord.pay_month.desc())
    ).all()
    period_map: dict[tuple[int, int], MonthlyPayrollPoint] = {}
    for s in salary_rows:
        key = (s.pay_year, s.pay_month)
        if key not in period_map:
            if len(period_map) >= 6:
                continue
            period_map[key] = MonthlyPayrollPoint(
                period=f"{s.pay_year}-{s.pay_month:02d}",
                total_net_salary=Decimal("0.00"),
                paid_amount=Decimal("0.00"),
                record_count=0,
            )
        point = period_map[key]
        point.total_net_salary += s.net_salary
        if s.payment_status == PaymentStatus.PAID:
            point.paid_amount += s.net_salary
        point.record_count += 1

    sorted_periods = [period_map[k] for k in sorted(period_map.keys())]
    latest_payroll_total = sorted_periods[-1].total_net_salary if sorted_periods else Decimal("0.00")

    recent_leave_rows = db.scalars(
        select(LeaveRequest)
        .options(
            joinedload(LeaveRequest.employee).joinedload(Employee.department),
            joinedload(LeaveRequest.reviewer),
        )
        .order_by(LeaveRequest.created_at.desc(), LeaveRequest.id.desc())
        .limit(5)
    ).all()

    return DashboardOverviewResponse(
        role=current_user.role.value,
        total_employees=total_employees,
        active_employees=active_employees,
        inactive_employees=inactive_employees,
        total_departments=total_departments,
        today_present=today_present,
        today_late=today_late,
        today_absent=today_absent,
        today_on_leave=today_on_leave,
        pending_leave_requests=pending_leaves,
        monthly_payroll_total=latest_payroll_total,
        department_stats=department_stats,
        attendance_trend=attendance_trend,
        payroll_trend=sorted_periods,
        recent_leaves=[serialize_leave(l) for l in recent_leave_rows],
        today_attendance=serialize_attendance(today_att_row) if today_att_row else None,
        latest_salary=serialize_salary(latest_salary_row) if latest_salary_row else None,
    )
