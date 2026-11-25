"""Idempotent database seeder for local development and portfolio demos."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.attendance import Attendance, AttendanceStatus
from app.models.department import Department
from app.models.employee import Employee, EmployeeStatus, EmploymentType
from app.models.leave import LeaveRequest, LeaveStatus, LeaveType
from app.models.salary import PaymentStatus, SalaryRecord
from app.models.user import User, UserRole


def seed_demo_data(db: Session) -> None:
    """Populate initial company records if the database has no users yet."""
    user_count = db.scalar(select(func.count(User.id))) or 0
    if user_count > 0:
        return

    # 1. Departments
    dept_eng = Department(name="Engineering", code="ENG", description="Core platform, API, and cloud engineering")
    dept_hr = Department(name="Human Resources", code="HR", description="Talent acquisition, culture, and people ops")
    dept_fin = Department(name="Finance", code="FIN", description="Accounting, payroll, and financial planning")
    dept_prod = Department(name="Product & Design", code="PRD", description="Product management and UX/UI design")
    dept_sales = Department(name="Sales & Growth", code="SLS", description="Enterprise sales and customer success")
    db.add_all([dept_eng, dept_hr, dept_fin, dept_prod, dept_sales])
    db.flush()

    # 2. Users + Employees
    admin_user = User(
        email="admin@company.com",
        full_name="Elena Vance",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    hr_user = User(
        email="hr@company.com",
        full_name="Marcus Chen",
        hashed_password=hash_password("HrManager@123"),
        role=UserRole.HR_MANAGER,
        is_active=True,
    )
    emp_user = User(
        email="employee@company.com",
        full_name="Sophia Patel",
        hashed_password=hash_password("Employee@123"),
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    dev_user = User(
        email="david.kim@company.com",
        full_name="David Kim",
        hashed_password=hash_password("Employee@123"),
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    db.add_all([admin_user, hr_user, emp_user, dev_user])
    db.flush()

    employees = [
        Employee(
            user_id=admin_user.id,
            employee_code="EMP-1001",
            first_name="Elena",
            last_name="Vance",
            email="admin@company.com",
            phone="+1-555-0101",
            department_id=dept_eng.id,
            job_title="VP of Engineering",
            employment_type=EmploymentType.FULL_TIME,
            status=EmployeeStatus.ACTIVE,
            hire_date=date(2022, 3, 14),
            base_salary=Decimal("12500.00"),
            address="420 Market St, San Francisco, CA",
            emergency_contact="Liam Vance (+1-555-0191)",
        ),
        Employee(
            user_id=hr_user.id,
            employee_code="EMP-1002",
            first_name="Marcus",
            last_name="Chen",
            email="hr@company.com",
            phone="+1-555-0102",
            department_id=dept_hr.id,
            job_title="HR Operations Manager",
            employment_type=EmploymentType.FULL_TIME,
            status=EmployeeStatus.ACTIVE,
            hire_date=date(2022, 7, 1),
            base_salary=Decimal("8200.00"),
            address="88 Howard St, San Francisco, CA",
            emergency_contact="Grace Chen (+1-555-0192)",
        ),
        Employee(
            user_id=emp_user.id,
            employee_code="EMP-1003",
            first_name="Sophia",
            last_name="Patel",
            email="employee@company.com",
            phone="+1-555-0103",
            department_id=dept_eng.id,
            job_title="Backend Software Engineer",
            employment_type=EmploymentType.FULL_TIME,
            status=EmployeeStatus.ACTIVE,
            hire_date=date(2023, 2, 10),
            base_salary=Decimal("7800.00"),
            address="1550 Mission St, San Francisco, CA",
            emergency_contact="Arjun Patel (+1-555-0193)",
        ),
        Employee(
            user_id=dev_user.id,
            employee_code="EMP-1004",
            first_name="David",
            last_name="Kim",
            email="david.kim@company.com",
            phone="+1-555-0104",
            department_id=dept_prod.id,
            job_title="Senior Product Designer",
            employment_type=EmploymentType.FULL_TIME,
            status=EmployeeStatus.ACTIVE,
            hire_date=date(2023, 5, 22),
            base_salary=Decimal("7600.00"),
            address="310 Townsend St, San Francisco, CA",
            emergency_contact="Hannah Kim (+1-555-0194)",
        ),
        Employee(
            employee_code="EMP-1005",
            first_name="Aisha",
            last_name="Rahman",
            email="aisha.rahman@company.com",
            phone="+1-555-0105",
            department_id=dept_fin.id,
            job_title="Financial Controller",
            employment_type=EmploymentType.FULL_TIME,
            status=EmployeeStatus.ACTIVE,
            hire_date=date(2023, 9, 4),
            base_salary=Decimal("8900.00"),
        ),
        Employee(
            employee_code="EMP-1006",
            first_name="Lucas",
            last_name="Moretti",
            email="lucas.moretti@company.com",
            phone="+1-555-0106",
            department_id=dept_sales.id,
            job_title="Enterprise Account Executive",
            employment_type=EmploymentType.FULL_TIME,
            status=EmployeeStatus.ACTIVE,
            hire_date=date(2024, 1, 15),
            base_salary=Decimal("6900.00"),
        ),
        Employee(
            employee_code="EMP-1007",
            first_name="Nora",
            last_name="Lindqvist",
            email="nora.lindqvist@company.com",
            phone="+1-555-0107",
            department_id=dept_eng.id,
            job_title="QA Automation Contractor",
            employment_type=EmploymentType.CONTRACT,
            status=EmployeeStatus.INACTIVE,
            hire_date=date(2024, 4, 8),
            base_salary=Decimal("5800.00"),
        ),
    ]
    db.add_all(employees)
    db.flush()

    dept_eng.manager_id = employees[0].id
    dept_hr.manager_id = employees[1].id
    dept_prod.manager_id = employees[3].id
    dept_fin.manager_id = employees[4].id
    dept_sales.manager_id = employees[5].id

    # 3. Attendance across the last 7 days
    today = date.today()
    active_emps = [e for e in employees if e.status == EmployeeStatus.ACTIVE]
    for day_offset in range(6, 0, -1):
        day = today - timedelta(days=day_offset)
        for idx, emp in enumerate(active_emps):
            check_in_dt = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=9, minutes=(idx * 7) % 45)
            check_out_dt = check_in_dt + timedelta(hours=8, minutes=15)
            att_status = AttendanceStatus.LATE if (day_offset + idx) % 7 == 0 else AttendanceStatus.PRESENT
            db.add(
                Attendance(
                    employee_id=emp.id,
                    date=day,
                    check_in=check_in_dt,
                    check_out=check_out_dt,
                    status=att_status,
                    work_hours=Decimal("8.25"),
                )
            )

    # Today's partial check-ins (leave Sophia unchecked-in or checked-in? Leave Sophia unchecked-in so she can test check-in!)
    for idx, emp in enumerate(active_emps):
        if emp.email == "employee@company.com":
            continue
        check_in_dt = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=9)
        db.add(
            Attendance(
                employee_id=emp.id,
                date=today,
                check_in=check_in_dt,
                status=AttendanceStatus.LATE if idx == 4 else AttendanceStatus.PRESENT,
            )
        )

    # 4. Leave requests
    db.add_all(
        [
            LeaveRequest(
                employee_id=employees[2].id,
                leave_type=LeaveType.ANNUAL,
                start_date=today + timedelta(days=5),
                end_date=today + timedelta(days=7),
                days_count=3,
                reason="Family trip planned out of town.",
                status=LeaveStatus.PENDING,
            ),
            LeaveRequest(
                employee_id=employees[3].id,
                leave_type=LeaveType.SICK,
                start_date=today - timedelta(days=12),
                end_date=today - timedelta(days=11),
                days_count=2,
                reason="Seasonal flu recovery.",
                status=LeaveStatus.APPROVED,
                reviewed_by=hr_user.id,
                reviewed_at=datetime.now(timezone.utc) - timedelta(days=12),
                review_comment="Approved. Rest well!",
            ),
            LeaveRequest(
                employee_id=employees[5].id,
                leave_type=LeaveType.CASUAL,
                start_date=today + timedelta(days=10),
                end_date=today + timedelta(days=10),
                days_count=1,
                reason="Personal appointment in the afternoon.",
                status=LeaveStatus.PENDING,
            ),
        ]
    )

    # 5. Salary records for the last 3 months
    for month_offset in range(2, -1, -1):
        ref_date = (today.replace(day=1) - timedelta(days=month_offset * 28)).replace(day=1)
        p_month = ref_date.month
        p_year = ref_date.year
        is_paid = month_offset > 0
        for emp in active_emps:
            allowances = (emp.base_salary * Decimal("0.12")).quantize(Decimal("0.01"))
            deductions = (emp.base_salary * Decimal("0.08")).quantize(Decimal("0.01"))
            net = emp.base_salary + allowances - deductions
            db.add(
                SalaryRecord(
                    employee_id=emp.id,
                    pay_month=p_month,
                    pay_year=p_year,
                    basic_salary=emp.base_salary,
                    allowances=allowances,
                    deductions=deductions,
                    net_salary=net,
                    payment_status=PaymentStatus.PAID if is_paid else PaymentStatus.PENDING,
                    payment_date=ref_date.replace(day=28) if is_paid else None,
                    notes="Monthly standard payroll run",
                    created_by=admin_user.id,
                )
            )

    db.commit()
