from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ...database import get_db
from ...models.task import Task, TaskStatus, TaskPriority
from ...models.user import User, UserRole
from ...models.project import Project
from ..deps import get_current_user
from pydantic import BaseModel

router = APIRouter()

class TaskCreate(BaseModel):
    project_id: int
    title: str
    description: Optional[str] = None
    assigned_to_id: Optional[int] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None

class TaskResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str]
    assigned_to_id: Optional[int]
    created_by_id: int
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date]
    project_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    project_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks"""
    query = db.query(Task)
    
    # Filter based on user role
    if current_user.role == UserRole.EMPLOYEE:
        query = query.filter(Task.assigned_to_id == current_user.id)
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.order_by(Task.due_date.asc()).all()
    
    # Enrich with project and user names
    result = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "project_id": task.project_id,
            "title": task.title,
            "description": task.description,
            "assigned_to_id": task.assigned_to_id,
            "created_by_id": task.created_by_id,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date,
            "project_name": task.project.name if task.project else None,
            "assigned_to_name": task.assigned_to.username if task.assigned_to else None
        }
        result.append(task_dict)
    
    return result

@router.get("/my-tasks", response_model=List[TaskResponse])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks assigned to current user"""
    tasks = db.query(Task).filter(
        Task.assigned_to_id == current_user.id
    ).order_by(Task.due_date.asc()).all()
    
    result = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "project_id": task.project_id,
            "title": task.title,
            "description": task.description,
            "assigned_to_id": task.assigned_to_id,
            "created_by_id": task.created_by_id,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date,
            "project_name": task.project.name if task.project else None,
            "assigned_to_name": current_user.username
        }
        result.append(task_dict)
    
    return result

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions
    if current_user.role == UserRole.EMPLOYEE and task.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "id": task.id,
        "project_id": task.project_id,
        "title": task.title,
        "description": task.description,
        "assigned_to_id": task.assigned_to_id,
        "created_by_id": task.created_by_id,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "project_name": task.project.name if task.project else None,
        "assigned_to_name": task.assigned_to.username if task.assigned_to else None
    }

@router.post("/", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new task"""
    # Check if project exists
    project = db.query(Project).filter(Project.id == task_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Only PM and Admin can create tasks
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.PROJECT_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized to create tasks")
    
    task = Task(
        project_id=task_data.project_id,
        title=task_data.title,
        description=task_data.description,
        assigned_to_id=task_data.assigned_to_id,
        created_by_id=current_user.id,
        priority=task_data.priority,
        due_date=task_data.due_date,
        status=TaskStatus.TODO
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return {
        "id": task.id,
        "project_id": task.project_id,
        "title": task.title,
        "description": task.description,
        "assigned_to_id": task.assigned_to_id,
        "created_by_id": task.created_by_id,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "project_name": project.name,
        "assigned_to_name": task.assigned_to.username if task.assigned_to else None
    }

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions
    if current_user.role == UserRole.EMPLOYEE and task.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.assigned_to_id is not None:
        task.assigned_to_id = task_data.assigned_to_id
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.due_date is not None:
        task.due_date = task_data.due_date
    
    db.commit()
    db.refresh(task)
    
    return {
        "id": task.id,
        "project_id": task.project_id,
        "title": task.title,
        "description": task.description,
        "assigned_to_id": task.assigned_to_id,
        "created_by_id": task.created_by_id,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "project_name": task.project.name if task.project else None,
        "assigned_to_name": task.assigned_to.username if task.assigned_to else None
    }

@router.patch("/{task_id}/status")
def update_task_status(
    task_id: int,
    status: TaskStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task status"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = status
    db.commit()
    
    return {"message": "Task status updated successfully"}

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete task"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}