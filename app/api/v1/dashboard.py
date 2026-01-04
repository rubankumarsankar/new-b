from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from ...database import get_db
from ...models.user import User, UserRole
from ...models.employee import Employee
from ...models.attendance import Attendance, AttendanceStatus
from ...models.project import Project, ProjectStatus
from ...models.task import Task, TaskStatus
from ...models.blog import Blog, BlogStatus
from ..deps import get_current_user

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for admin users"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        return {"error": "Not authorized"}
    
    today = date.today()
    
    # Total employees
    total_employees = db.query(Employee).count()
    
    # Present today
    present_today = db.query(Attendance).filter(
        Attendance.date == today,
        Attendance.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE])
    ).count()
    
    # Active projects
    active_projects = db.query(Project).filter(
        Project.status == ProjectStatus.ACTIVE
    ).count()
    
    # Pending tasks
    pending_tasks = db.query(Task).filter(
        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
    ).count()
    
    # Draft blogs
    draft_blogs = db.query(Blog).filter(
        Blog.status == BlogStatus.DRAFT
    ).count()
    
    # Late arrivals today
    late_today = db.query(Attendance).filter(
        Attendance.date == today,
        Attendance.status == AttendanceStatus.LATE
    ).count()
    
    # Overdue tasks
    overdue_tasks = db.query(Task).filter(
        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
        Task.due_date < today
    ).count()
    
    return {
        "total_employees": total_employees,
        "present_today": present_today,
        "active_projects": active_projects,
        "pending_tasks": pending_tasks,
        "draft_blogs": draft_blogs,
        "late_arrivals_today": late_today,
        "overdue_tasks": overdue_tasks
    }

@router.get("/employee-stats")
def get_employee_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for employees"""
    today = date.today()
    
    # My pending tasks
    pending_tasks = db.query(Task).filter(
        Task.assigned_to_id == current_user.id,
        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
    ).count()
    
    # My completed tasks this month
    completed_tasks = db.query(Task).filter(
        Task.assigned_to_id == current_user.id,
        Task.status == TaskStatus.COMPLETED,
        func.month(Task.completed_at) == today.month,
        func.year(Task.completed_at) == today.year
    ).count()
    
    # Active projects I'm involved in
    active_projects = db.query(Project).join(Task).filter(
        Task.assigned_to_id == current_user.id,
        Project.status == ProjectStatus.ACTIVE
    ).distinct().count()
    
    # My overdue tasks
    overdue_tasks = db.query(Task).filter(
        Task.assigned_to_id == current_user.id,
        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
        Task.due_date < today
    ).count()
    
    return {
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "active_projects": active_projects,
        "overdue_tasks": overdue_tasks
    }