from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import secrets
import string
from ...database import get_db
from ...models.employee import Employee
from ...models.user import User, UserRole
from ...core.security import get_password_hash, verify_password
from ...services.email import email_service
from ..deps import get_current_user
from pydantic import BaseModel, EmailStr

router = APIRouter()

def generate_random_password(length=12):
    """Generate a secure random password"""
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*"
    
    # Ensure at least one of each type
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Fill the rest randomly
    all_chars = uppercase + lowercase + digits + special
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

class EmployeeCreate(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    date_of_joining: Optional[date] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    role: UserRole = UserRole.EMPLOYEE

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
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
    email: str
    phone: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    date_of_joining: Optional[date]
    date_of_birth: Optional[date]
    address: Optional[str]
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

class EmployeeCreateResponse(EmployeeResponse):
    """Response with temporary password"""
    temp_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
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
            "email": emp.user.email if emp.user else None,
            "phone": emp.phone,
            "department": emp.department,
            "designation": emp.designation,
            "date_of_joining": emp.date_of_joining,
            "date_of_birth": emp.date_of_birth,
            "address": emp.address,
            "role": emp.user.role.value if emp.user else None,
            "is_active": emp.user.is_active if emp.user else False
        }
        result.append(emp_dict)
    
    return result

@router.get("/me", response_model=EmployeeResponse)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's employee profile"""
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    return {
        "id": employee.id,
        "user_id": employee.user_id,
        "employee_code": employee.employee_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": current_user.email,
        "phone": employee.phone,
        "department": employee.department,
        "designation": employee.designation,
        "date_of_joining": employee.date_of_joining,
        "date_of_birth": employee.date_of_birth,
        "address": employee.address,
        "role": current_user.role.value,
        "is_active": current_user.is_active
    }

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
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
        "email": employee.user.email if employee.user else None,
        "phone": employee.phone,
        "department": employee.department,
        "designation": employee.designation,
        "date_of_joining": employee.date_of_joining,
        "date_of_birth": employee.date_of_birth,
        "address": employee.address,
        "role": employee.user.role.value if employee.user else None,
        "is_active": employee.user.is_active if employee.user else False
    }

@router.post("/", response_model=EmployeeCreateResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new employee with auto-generated user account and password"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if employee code exists
    if db.query(Employee).filter(Employee.employee_code == employee_data.employee_code).first():
        raise HTTPException(status_code=400, detail="Employee code already exists")
    
    # Check if email already exists
    if db.query(User).filter(User.email == employee_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate username from email
    username = employee_data.email.split('@')[0]
    
    # Check if username exists, if yes, append employee code
    if db.query(User).filter(User.username == username).first():
        username = f"{username}_{employee_data.employee_code}"
    
    # Generate secure random password
    temp_password = generate_random_password()
    
    # Create user account
    user = User(
        email=employee_data.email,
        username=username,
        hashed_password=get_password_hash(temp_password),
        role=employee_data.role,
        is_active=True
    )
    
    db.add(user)
    db.flush()
    
    # Create employee profile
    employee = Employee(
        user_id=user.id,
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
    db.refresh(user)
    
    # Send welcome email in background
    employee_name = f"{employee.first_name} {employee.last_name}"
    background_tasks.add_task(
        email_service.send_welcome_email,
        name=employee_name,
        email=user.email,
        username=username,
        password=temp_password
    )
    
    print(f"✅ Employee created - Username: {username}, Password: {temp_password}")
    print(f"📧 Welcome email queued for {user.email}")
    
    return {
        "id": employee.id,
        "user_id": user.id,
        "employee_code": employee.employee_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": user.email,
        "phone": employee.phone,
        "department": employee.department,
        "designation": employee.designation,
        "date_of_joining": employee.date_of_joining,
        "date_of_birth": employee.date_of_birth,
        "address": employee.address,
        "role": user.role.value,
        "is_active": user.is_active,
        "temp_password": temp_password
    }

@router.put("/me", response_model=EmployeeResponse)
async def update_my_profile(
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile"""
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    # Update employee fields
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
    
    # Update user email if provided
    if employee_data.email is not None:
        existing_user = db.query(User).filter(
            User.email == employee_data.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = employee_data.email
    
    db.commit()
    db.refresh(employee)
    db.refresh(current_user)
    
    return {
        "id": employee.id,
        "user_id": current_user.id,
        "employee_code": employee.employee_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": current_user.email,
        "phone": employee.phone,
        "department": employee.department,
        "designation": employee.designation,
        "date_of_joining": employee.date_of_joining,
        "date_of_birth": employee.date_of_birth,
        "address": employee.address,
        "role": current_user.role.value,
        "is_active": current_user.is_active
    }

@router.post("/me/change-password")
async def change_my_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change current user's password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=400, 
            detail="New password must be at least 8 characters long"
        )
    
    # Check if new password is same as current
    if verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400, 
            detail="New password must be different from current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update employee (Admin only)"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    user = employee.user
    
    # Update employee fields
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
    
    # Update user email if provided
    if employee_data.email is not None:
        existing_user = db.query(User).filter(
            User.email == employee_data.email,
            User.id != user.id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = employee_data.email
    
    db.commit()
    db.refresh(employee)
    db.refresh(user)
    
    return {
        "id": employee.id,
        "user_id": user.id,
        "employee_code": employee.employee_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": user.email,
        "phone": employee.phone,
        "department": employee.department,
        "designation": employee.designation,
        "date_of_joining": employee.date_of_joining,
        "date_of_birth": employee.date_of_birth,
        "address": employee.address,
        "role": user.role.value,
        "is_active": user.is_active
    }

@router.post("/{employee_id}/reset-password")
async def reset_employee_password(
    employee_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset employee password (Admin only)"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    user = employee.user
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new password
    new_password = generate_random_password()
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    # Send password reset email in background
    employee_name = f"{employee.first_name} {employee.last_name}"
    background_tasks.add_task(
        email_service.send_password_reset_email,
        name=employee_name,
        email=user.email,
        username=user.username,
        password=new_password
    )
    
    print(f"✅ Password reset for {user.username}: {new_password}")
    print(f"📧 Password reset email queued for {user.email}")
    
    return {
        "message": "Password reset successfully",
        "username": user.username,
        "temp_password": new_password
    }

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete employee and associated user account (Admin only)"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Prevent deleting own account
    if employee.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user_id = employee.user_id
    
    # Delete employee
    db.delete(employee)
    
    # Delete associated user account
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
    
    db.commit()
    
    return {"message": "Employee and user account deleted successfully"}