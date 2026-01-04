from sqlalchemy import Column, Integer, Date, Time, ForeignKey, String, Enum, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    LATE = "late"
    HALF_DAY = "half_day"
    ABSENT = "absent"
    LEAVE = "leave"

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    check_in_time = Column(Time)
    check_out_time = Column(Time)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.ABSENT)
    working_hours = Column(Float, default=0.0)
    remarks = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")