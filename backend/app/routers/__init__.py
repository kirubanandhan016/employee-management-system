"""Aggregate API router exports."""

from fastapi import APIRouter

from app.routers import attendance, auth, dashboard, departments, employees, leaves, salaries, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(employees.router)
api_router.include_router(attendance.router)
api_router.include_router(leaves.router)
api_router.include_router(salaries.router)
api_router.include_router(dashboard.router)
