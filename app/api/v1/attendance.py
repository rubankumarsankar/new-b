from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, time
from typing import List, Optional
from ...database import get_db
from ...models.attendance import Attendance, AttendanceStatus
from ...models.employee import Employee
from ...models.user import User, UserRole
from ..deps import get_current_user
from ...config import settings
from pydantic import BaseModel

router = APIRouter()

class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in_time: Optional[time]
    check_out_time: Optional[time]
    status: AttendanceStatus
    working_hours: float
    
    class Config:
        from_attributes = True

def calculate_status(check_in_time: time) -> AttendanceStatus:
    """Calculate attendance status based on check-in time"""
    office_start = datetime.strptime(settings.OFFICE_START_TIME, "%H:%M").time()
    grace_minutes = settings.GRACE_PERIOD_MINUTES
    
    check_in_datetime = datetime.combine(date.today(), check_in_time)
    office_start_datetime = datetime.combine(date.today(), office_start)
    
    diff_minutes = (check_in_datetime - office_start_datetime).total_seconds() / 60
    
    if diff_minutes <= grace_minutes:
        return AttendanceStatus.PRESENT
    else:
        return AttendanceStatus.LATE

def calculate_working_hours(check_in: time, check_out: time) -> float:
    """Calculate working hours between check-in and check-out"""
    check_in_dt = datetime.combine(date.today(), check_in)
    check_out_dt = datetime.combine(date.today(), check_out)
    
    diff = check_out_dt - check_in_dt
    hours = diff.total_seconds() / 3600
    return round(hours, 2)

@router.post("/check-in", response_model=AttendanceResponse)
def check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check in for the day"""
    # Get employee
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    # Check if already checked in today
    today = date.today()
    existing = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.date == today
    ).first()
    
    if existing and existing.check_in_time:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    check_in_time = datetime.now().time()
    status = calculate_status(check_in_time)
    
    if existing:
        existing.check_in_time = check_in_time
        existing.status = status
        db.commit()
        db.refresh(existing)
        return existing
    else:
        attendance = Attendance(
            employee_id=employee.id,
            date=today,
            check_in_time=check_in_time,
            status=status
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

@router.post("/check-out", response_model=AttendanceResponse)
def check_out(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check out for the day"""
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    today = date.today()
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.date == today
    ).first()
    
    if not attendance or not attendance.check_in_time:
        raise HTTPException(status_code=400, detail="Please check in first")
    
    if attendance.check_out_time:
        raise HTTPException(status_code=400, detail="Already checked out")
    
    check_out_time = datetime.now().time()
    attendance.check_out_time = check_out_time
    attendance.working_hours = calculate_working_hours(
        attendance.check_in_time,
        check_out_time
    )
    
    db.commit()
    db.refresh(attendance)
    return attendance

@router.get("/today", response_model=Optional[AttendanceResponse])
def get_today_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get today's attendance for current user"""
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        return None
    
    today = date.today()
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.date == today
    ).first()
    
    return attendance

@router.get("/history", response_model=List[AttendanceResponse])
def get_attendance_history(
    skip: int = 0,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attendance history for current user"""
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        return []
    
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee.id
    ).order_by(Attendance.date.desc()).offset(skip).limit(limit).all()
    
    return attendance

@router.get("/all-today", response_model=List[dict])
def get_all_today_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all employees' attendance for today (Admin only)"""
    # Only admin can view all attendance
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    today = date.today()
    attendance = db.query(Attendance, Employee, User).join(
        Employee, Attendance.employee_id == Employee.id
    ).join(
        User, Employee.user_id == User.id
    ).filter(
        Attendance.date == today
    ).all()
    
    return [
        {
            "id": att.id,
            "employee_name": f"{emp.first_name} {emp.last_name}",
            "check_in_time": att.check_in_time.strftime("%H:%M") if att.check_in_time else None,
            "check_out_time": att.check_out_time.strftime("%H:%M") if att.check_out_time else None,
            "status": att.status.value,
            "working_hours": att.working_hours
        }
        for att, emp, user in attendance
    ]