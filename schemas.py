from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str
    user_id: int


class EmployeeCreate(BaseModel):
    employee_id: str
    name: str
    email: str
    password: str
    department: str
    designation: str = ""
    phone: str = ""
    address: str = ""
    joining_date: Optional[date] = None
    basic_salary: float = 0.0


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    basic_salary: Optional[float] = None
    is_active: Optional[bool] = None


class EmployeeOut(BaseModel):
    id: int
    employee_id: Optional[str]
    name: str
    email: str
    role: str
    department: Optional[str]
    designation: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    joining_date: Optional[date]
    basic_salary: Optional[float]
    is_active: bool

    class Config:
        from_attributes = True


class AttendanceLocation(BaseModel):
    latitude: float
    longitude: float


class LeaveCreate(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str = ""


class LeaveUpdate(BaseModel):
    status: str  # approved | rejected


class LeaveOut(BaseModel):
    id: int
    user_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str]
    status: str

    class Config:
        from_attributes = True


class PayslipGenerate(BaseModel):
    employee_id: int
    month: int
    year: int


class RecruitmentCreate(BaseModel):
    position: str
    department: str
    description: str = ""
    vacancies: int = 1
