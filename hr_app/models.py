from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, date
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="employee")  # ceo | hr_admin | employee
    department = Column(String, default="")
    designation = Column(String, default="")
    phone = Column(String, default="")
    address = Column(Text, default="")
    joining_date = Column(Date, default=date.today)
    basic_salary = Column(Float, default=0.0)
    profile_photo = Column(String, default="")
    is_active = Column(Boolean, default=True)
    face_descriptor = Column(Text, nullable=True)  # JSON 128-d float array from face-api.js
    created_at = Column(DateTime, default=datetime.utcnow)

    attendance = relationship("Attendance", back_populates="user", cascade="all, delete")
    leaves = relationship("Leave", back_populates="user", cascade="all, delete")
    payslips = relationship("Payslip", back_populates="user", cascade="all, delete")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete")


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, default=date.today)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    hours_worked = Column(Float, default=0.0)
    status = Column(String, default="absent")  # present | absent | half_day

    user = relationship("User", back_populates="attendance")


class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    leave_type = Column(String)  # sick | casual | annual | maternity | unpaid
    start_date = Column(Date)
    end_date = Column(Date)
    reason = Column(Text, default="")
    status = Column(String, default="pending")  # pending | approved | rejected
    approved_by = Column(Integer, nullable=True)
    applied_on = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="leaves")


class Payslip(Base):
    __tablename__ = "payslips"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    month = Column(Integer)
    year = Column(Integer)
    basic_salary = Column(Float, default=0.0)
    hra = Column(Float, default=0.0)
    travel_allowance = Column(Float, default=0.0)
    da = Column(Float, default=0.0)
    pf_deduction = Column(Float, default=0.0)
    tax_deduction = Column(Float, default=0.0)
    net_salary = Column(Float, default=0.0)
    pdf_path = Column(String, default="")
    generated_on = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payslips")


class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    file_path = Column(String)
    uploaded_on = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")


class Recruitment(Base):
    __tablename__ = "recruitments"
    id = Column(Integer, primary_key=True, index=True)
    position = Column(String)
    department = Column(String)
    description = Column(Text, default="")
    vacancies = Column(Integer, default=1)
    status = Column(String, default="open")  # open | closed | on_hold
    posted_on = Column(DateTime, default=datetime.utcnow)
    posted_by = Column(Integer, ForeignKey("users.id"), nullable=True)


# face descriptor stored as JSON string (128-dim float array from face-api.js)
# Added to User model via ALTER pattern for SQLite compatibility
from sqlalchemy import event, text

def add_face_descriptor_column(target, connection, **kw):
    try:
        connection.execute(text("ALTER TABLE users ADD COLUMN face_descriptor TEXT"))
    except Exception:
        pass  # column already exists

event.listen(models_Base := models_Base if False else __import__('database').Base.metadata, 'after_create', lambda *a, **kw: None)
