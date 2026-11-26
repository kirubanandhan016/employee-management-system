# PeoplePulse EMS — System Architecture

```mermaid
flowchart TD
  Browser[React + Vite frontend] --> Nginx[Nginx frontend container]
  Nginx --> API[FastAPI backend]
  API --> Auth[JWT authentication and RBAC dependencies]
  API --> Routers[Versioned REST routers]
  Routers --> Services[Business services]
  Services --> ORM[SQLAlchemy 2.0 models]
  ORM --> DB[(PostgreSQL)]
  Migrations[Alembic] --> DB
  Tests[Pytest backend suite] --> API
```

The React client calls the FastAPI API. Authentication and role-based dependencies protect administrative, HR, and employee workflows. Services implement business rules; SQLAlchemy persists records; Alembic manages schema revisions.
