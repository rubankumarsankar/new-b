from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ...database import get_db
from ...models.employee import Employee
from ...models.user import User, UserRole
from ..deps import get_current_user
from pydantic import BaseModel

router = APIRouter()

class EmployeeCreate(BaseModel):
    user_id: int
    employee_code: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    date_of_joining: Optional[date] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    date_of_joining: Optional[date] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    user_id: int
    employee_code: str
    first_name: str
    last_name: str
    phone: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    date_of_joining: Optional[date]
    date_of_birth: Optional[date]
    address: Optional[str]
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[EmployeeResponse])
def get_employees(
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all employees (Admin only)"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Employee)
    
    if department:
        query = query.filter(Employee.department == department)
    
    employees = query.all()
    
    # Enrich with user data
    result = []
    for emp in employees:
        emp_dict = {
            "id": emp.id,
            "user_id": emp.user_id,
            "employee_code": emp.employee_code,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "phone": emp.phone,
            "department": emp.department,
            "designation": emp.designation,
            "date_of_joining": emp.date_of_joining,
            "date_of_birth": emp.date_of_birth,
            "address": emp.address,
            "email": emp.user.email if emp.user else None,
            "username": emp.user.username if emp.user else None,
            "role": emp.user.role.value if emp.user else None
        }
        result.append(emp_dict)
    
    return result

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee by ID"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check permissions
    if current_user.role == UserRole.EMPLOYEE:
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not emp or emp.id != employee_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "id": employee.id,
        "user_id": employee.user_id,
        "employee_code": employee.employee_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "phone": employee.phone,
        "department": employee.department,
        "designation": employee.designation,
        "date_of_joining": employee.date_of_joining,
        "date_of_birth": employee.date_of_birth,
        "address": employee.address,
        "email": employee.user.email if employee.user else None,
        "username": employee.user.username if employee.user else None,
        "role": employee.user.role.value if employee.user else None
    }

@router.post("/", response_model=EmployeeResponse)
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new employee (Admin only)"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if employee code exists
    if db.query(Employee).filter(Employee.employee_code == employee_data.employee_code).first():
        raise HTTPException(status_code=400, detail="Employee code already exists")
    
    # Check if user exists
    user = db.query(User).filter(User.id == employee_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user already has employee profile
    if db.query(Employee).filter(Employee.user_id == employee_data.user_id).first():
        raise HTTPException(status_code=400, detail="User already has an employee profile")
    
    employee = Employee(
        user_id=employee_data.user_id,
        employee_code=employee_data.employee_code,
        first_name=employee_data.first_name,
        last_name=employee_data.last_name,
        phone=employee_data.phone,
        department=employee_data.department,
        designation=employee_data.designation,
        date_of_joining=employee_data.date_of_joining,
        date_of_birth=employee_data.date_of_birth,
        address=employee_data.address
    )
    
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return {
        "id": employee.id,
        "user_id": employee.user_id,
        "employee_code": employee.employee_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "phone": employee.phone,
        "department": employee.department,
        "designation": employee.designation,
        "date_of_joining": employee.date_of_joining,
        "date_of_birth": employee.date_of_birth,
        "address": employee.address,
        "email": user.email,
        "username": user.username,
        "role": user.role.value
    }

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update employee"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if employee_data.first_name is not None:
        employee.first_name = employee_data.first_name
    if employee_data.last_name is not None:
        employee.last_name = employee_data.last_name
    if employee_data.phone is not None:
        employee.phone = employee_data.phone
    if employee_data.department is not None:
        employee.department = employee_data.department
    if employee_data.designation is not None:
        employee.designation = employee_data.designation
    if employee_data.date_of_joining is not None:
        employee.date_of_joining = employee_data.date_of_joining
    if employee_data.date_of_birth is not None:
        employee.date_of_birth = employee_data.date_of_birth
    if employee_data.address is not None:
        employee.address = employee_data.address
    
    db.commit()
    db.refresh(employee)
    
    return {
        "id": employee.id,
        "user_id": employee.user_id,
        "employee_code": employee.employee_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "phone": employee.phone,
        "department": employee.department,
        "designation": employee.designation,
        "date_of_joining": employee.date_of_joining,
        "date_of_birth": employee.date_of_birth,
        "address": employee.address,
        "email": employee.user.email if employee.user else None,
        "username": employee.user.username if employee.user else None,
        "role": employee.user.role.value if employee.user else None
    }

@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete employee"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(employee)
    db.commit()
    
    return {"message": "Employee deleted successfully"}