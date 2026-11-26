# PeoplePulse EMS — Database ER Diagram

```mermaid
erDiagram
  USERS ||--o| EMPLOYEES : links_to
  DEPARTMENTS ||--o{ EMPLOYEES : contains
  EMPLOYEES ||--o{ ATTENDANCE : logs
  EMPLOYEES ||--o{ LEAVE_REQUESTS : submits
  USERS ||--o{ LEAVE_REQUESTS : reviews
  EMPLOYEES ||--o{ SALARY_RECORDS : receives
  USERS ||--o{ SALARY_RECORDS : creates
  USERS {
    int id PK
    string email UK
    string full_name
    string hashed_password
    string role
    bool is_active
  }
  DEPARTMENTS {
    int id PK
    string name UK
    string code UK
    int manager_id FK
  }
  EMPLOYEES {
    int id PK
    int user_id FK
    string employee_code UK
    int department_id FK
    string job_title
    date hire_date
  }
  ATTENDANCE {
    int id PK
    int employee_id FK
    date date
    datetime check_in
    datetime check_out
  }
  LEAVE_REQUESTS {
    int id PK
    int employee_id FK
    int reviewed_by FK
    date start_date
    date end_date
    string status
  }
  SALARY_RECORDS {
    int id PK
    int employee_id FK
    int pay_month
    int pay_year
    numeric net_salary
  }
```

This diagram follows the entities and relationships documented in the repository README. Verify exact column names, enum values, and constraints against `backend/app/models/` and Alembic revisions before using it as a migration specification.
