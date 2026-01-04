from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ...database import get_db
from ...models.project import Project, ProjectStatus
from ...models.employee import Employee
from ...models.user import User, UserRole
from ..deps import get_current_user
from pydantic import BaseModel

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[int] = None
    status: Optional[ProjectStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    manager_id: Optional[int]
    status: ProjectStatus
    start_date: Optional[date]
    end_date: Optional[date]
    manager_name: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[ProjectResponse])
def get_projects(
    status: Optional[ProjectStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all projects"""
    query = db.query(Project)
    
    if status:
        query = query.filter(Project.status == status)
    
    projects = query.all()
    
    # Enrich with manager name
    result = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "name": project.name,
            "code": project.code,
            "description": project.description,
            "manager_id": project.manager_id,
            "status": project.status,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "manager_name": None
        }
        
        if project.manager:
            project_dict["manager_name"] = f"{project.manager.first_name} {project.manager.last_name}"
        
        result.append(project_dict)
    
    return result

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "id": project.id,
        "name": project.name,
        "code": project.code,
        "description": project.description,
        "manager_id": project.manager_id,
        "status": project.status,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "manager_name": f"{project.manager.first_name} {project.manager.last_name}" if project.manager else None
    }

@router.post("/", response_model=ProjectResponse)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new project"""
    # Only admin and PM can create projects
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.PROJECT_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if code already exists
    if db.query(Project).filter(Project.code == project_data.code).first():
        raise HTTPException(status_code=400, detail="Project code already exists")
    
    project = Project(
        name=project_data.name,
        code=project_data.code,
        description=project_data.description,
        manager_id=project_data.manager_id,
        status=project_data.status,
        start_date=project_data.start_date,
        end_date=project_data.end_date
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return {
        "id": project.id,
        "name": project.name,
        "code": project.code,
        "description": project.description,
        "manager_id": project.manager_id,
        "status": project.status,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "manager_name": f"{project.manager.first_name} {project.manager.last_name}" if project.manager else None
    }

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.manager_id is not None:
        project.manager_id = project_data.manager_id
    if project_data.status is not None:
        project.status = project_data.status
    if project_data.start_date is not None:
        project.start_date = project_data.start_date
    if project_data.end_date is not None:
        project.end_date = project_data.end_date
    
    db.commit()
    db.refresh(project)
    
    return {
        "id": project.id,
        "name": project.name,
        "code": project.code,
        "description": project.description,
        "manager_id": project.manager_id,
        "status": project.status,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "manager_name": f"{project.manager.first_name} {project.manager.last_name}" if project.manager else None
    }

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete project"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}