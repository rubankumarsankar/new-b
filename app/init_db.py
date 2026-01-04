"""
Initialize database with sample data
Run this script after setting up the database:
python init_db.py
"""

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.project import Project, ProjectStatus
from app.models.settings import SystemSettings
from app.core.security import get_password_hash
from datetime import date

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(User).first():
            print("Database already initialized!")
            return
        
        print("Initializing database...")
        
        # Create Super Admin
        super_admin = User(
            email="superadmin@phase1.com",
            username="superadmin",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        
        # Create Admin
        admin = User(
            email="admin@phase1.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        # Create Project Manager
        pm = User(
            email="pm@phase1.com",
            username="pmuser",
            hashed_password=get_password_hash("pm123"),
            role=UserRole.PROJECT_MANAGER,
            is_active=True
        )
        db.add(pm)
        db.commit()
        db.refresh(pm)
        
        # Create Employee
        emp_user = User(
            email="employee@phase1.com",
            username="employee",
            hashed_password=get_password_hash("emp123"),
            role=UserRole.EMPLOYEE,
            is_active=True
        )
        db.add(emp_user)
        db.commit()
        db.refresh(emp_user)
        
        # Create Content Editor
        editor = User(
            email="editor@phase1.com",
            username="editor",
            hashed_password=get_password_hash("editor123"),
            role=UserRole.CONTENT_EDITOR,
            is_active=True
        )
        db.add(editor)
        db.commit()
        db.refresh(editor)
        
        # Create Employee Profiles
        admin_emp = Employee(
            user_id=admin.id,
            employee_code="EMP001",
            first_name="Admin",
            last_name="User",
            phone="1234567890",
            department="Management",
            designation="Administrator",
            date_of_joining=date(2024, 1, 1)
        )
        db.add(admin_emp)
        
        pm_emp = Employee(
            user_id=pm.id,
            employee_code="EMP002",
            first_name="Project",
            last_name="Manager",
            phone="1234567891",
            department="Development",
            designation="Project Manager",
            date_of_joining=date(2024, 1, 15)
        )
        db.add(pm_emp)
        
        emp_emp = Employee(
            user_id=emp_user.id,
            employee_code="EMP003",
            first_name="John",
            last_name="Doe",
            phone="1234567892",
            department="Development",
            designation="Software Developer",
            date_of_joining=date(2024, 2, 1)
        )
        db.add(emp_emp)
        
        editor_emp = Employee(
            user_id=editor.id,
            employee_code="EMP004",
            first_name="Jane",
            last_name="Smith",
            phone="1234567893",
            department="Marketing",
            designation="Content Writer",
            date_of_joining=date(2024, 2, 15)
        )
        db.add(editor_emp)
        
        db.commit()
        db.refresh(pm_emp)
        
        # Create Sample Project
        project = Project(
            name="Phase-1 Development",
            code="PRJ001",
            description="Main development project for Phase-1 system",
            manager_id=pm_emp.id,
            status=ProjectStatus.ACTIVE,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        db.add(project)
        
        project2 = Project(
            name="Marketing Campaign",
            code="PRJ002",
            description="Q1 Marketing campaign project",
            manager_id=pm_emp.id,
            status=ProjectStatus.PLANNING,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 6, 30)
        )
        db.add(project2)
        
        # Create System Settings
        settings = [
            SystemSettings(
                key="office_start_time",
                value="09:30",
                description="Office start time",
                category="attendance"
            ),
            SystemSettings(
                key="office_end_time",
                value="18:30",
                description="Office end time",
                category="attendance"
            ),
            SystemSettings(
                key="grace_period_minutes",
                value="15",
                description="Grace period for late arrival",
                category="attendance"
            ),
            SystemSettings(
                key="enable_teams_notifications",
                value="true",
                description="Enable Microsoft Teams notifications",
                category="notification"
            ),
            SystemSettings(
                key="enable_outlook_calendar",
                value="true",
                description="Enable Outlook calendar integration",
                category="notification"
            ),
            SystemSettings(
                key="min_working_hours",
                value="8",
                description="Minimum working hours per day",
                category="attendance"
            ),
            SystemSettings(
                key="task_overdue_notification",
                value="true",
                description="Send notification for overdue tasks",
                category="task"
            )
        ]
        
        for setting in settings:
            db.add(setting)
        
        db.commit()
        
        print("\n" + "="*60)
        print("✅ Database initialized successfully!")
        print("="*60)
        print("\n📊 DEFAULT USERS CREATED:")
        print("-" * 60)
        print("1. Super Admin")
        print("   Username: superadmin")
        print("   Password: admin123")
        print("   Access: Full system control")
        print()
        print("2. Admin")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Access: Office & project control")
        print()
        print("3. Project Manager")
        print("   Username: pmuser")
        print("   Password: pm123")
        print("   Access: Project & task management")
        print()
        print("4. Employee")
        print("   Username: employee")
        print("   Password: emp123")
        print("   Access: Daily work & attendance")
        print()
        print("5. Content Editor")
        print("   Username: editor")
        print("   Password: editor123")
        print("   Access: Blog management")
        print("-" * 60)
        print("\n🚀 You can now start the server:")
        print("   uvicorn app.main:app --reload")
        print()
        print("📚 API Documentation will be available at:")
        print("   http://localhost:8000/docs")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()