# PeoplePulse EMS — API Examples

Run the stack with Docker Compose, then open [Swagger UI](http://localhost:8000/docs). The OpenAPI schema served by the running backend is authoritative.

## Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{"email":"employee@example.com","password":"<local-demo-password>"}
```

## Read the current employee profile
```http
GET /api/v1/employees/me
Authorization: Bearer <access_token>
```

## Check in
```http
POST /api/v1/attendance/check-in
Authorization: Bearer <access_token>
```

## Submit a leave request
```http
POST /api/v1/leaves
Authorization: Bearer <access_token>
Content-Type: application/json

{"leave_type":"annual","start_date":"2026-12-01","end_date":"2026-12-02"}
```

Use the current Swagger request schemas to confirm field names and required payloads. Do not use real employee information in screenshots or public examples.
