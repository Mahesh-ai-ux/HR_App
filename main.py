from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
import os

from database import get_db, engine, SessionLocal
import models, schemas, auth, utils

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nexila HR System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Geofence — Nexila Technologies, West Tambaram, Chennai
OFFICE_LAT = 12.9291
OFFICE_LNG = 80.1003
GEOFENCE_RADIUS_M = 500  # metres (configurable)


# ══════════════════════════════════════════════════════
#  STARTUP SEED
# ══════════════════════════════════════════════════════
@app.on_event("startup")
def seed_defaults():
    db = SessionLocal()
    try:
        if not db.query(models.User).first():
            defaults = [
                models.User(employee_id="CEO001", name="Raj Prabhu", email="ceo@nexila.com",
                            password_hash=auth.hash_password("ceo123"), role="ceo",
                            department="Executive", designation="Chief Executive Officer",
                            basic_salary=200000, phone="9876543210"),
                models.User(employee_id="HR001", name="Priya Sharma", email="hr@nexila.com",
                            password_hash=auth.hash_password("hr123"), role="hr_admin",
                            department="Human Resources", designation="HR Manager",
                            basic_salary=80000, phone="9876500001"),
                models.User(employee_id="EMP001", name="Arjun Nair", email="arjun@nexila.com",
                            password_hash=auth.hash_password("emp123"), role="employee",
                            department="Engineering", designation="Senior Software Engineer",
                            basic_salary=65000, phone="9876500002",
                            joining_date=date(2023, 3, 1)),
                models.User(employee_id="EMP002", name="Divya Menon", email="divya@nexila.com",
                            password_hash=auth.hash_password("emp456"), role="employee",
                            department="Design", designation="UI/UX Designer",
                            basic_salary=55000, phone="9876500003",
                            joining_date=date(2023, 6, 15)),
            ]
            db.add_all(defaults)
            db.commit()
    finally:
        db.close()


# ══════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════
@app.post("/api/auth/login", response_model=schemas.Token)
def login(creds: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == creds.email).first()
    if not user or not auth.verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer",
            "role": user.role, "name": user.name, "user_id": user.id}


# ══════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════
@app.get("/api/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    today = date.today()
    stats = {
        "total_employees": db.query(models.User).filter(models.User.role == "employee").count(),
        "present_today": db.query(models.Attendance).filter(
            models.Attendance.date == today, models.Attendance.status == "present").count(),
        "pending_leaves": db.query(models.Leave).filter(models.Leave.status == "pending").count(),
        "total_payslips": db.query(models.Payslip).count(),
        "open_positions": db.query(models.Recruitment).filter(models.Recruitment.status == "open").count(),
    }
    if me.role == "employee":
        my_leaves = db.query(models.Leave).filter(models.Leave.user_id == me.id).count()
        my_att = db.query(models.Attendance).filter(
            models.Attendance.user_id == me.id, models.Attendance.status == "present").count()
        today_att = db.query(models.Attendance).filter(
            models.Attendance.user_id == me.id, models.Attendance.date == today).first()
        stats["my_leaves"] = my_leaves
        stats["my_present_days"] = my_att
        stats["checked_in_today"] = bool(today_att and today_att.check_in)
        stats["checked_out_today"] = bool(today_att and today_att.check_out)
    return stats


# ══════════════════════════════════════════════════════
#  EMPLOYEES
# ══════════════════════════════════════════════════════
@app.get("/api/employees", response_model=List[schemas.EmployeeOut])
def list_employees(db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role not in ["ceo", "hr_admin"]:
        raise HTTPException(403, "Forbidden")
    return db.query(models.User).filter(models.User.role == "employee").all()


@app.get("/api/employees/me", response_model=schemas.EmployeeOut)
def my_profile(db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    return me


@app.get("/api/employees/{emp_id}", response_model=schemas.EmployeeOut)
def get_employee(emp_id: int, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role not in ["ceo", "hr_admin"] and me.id != emp_id:
        raise HTTPException(403, "Forbidden")
    emp = db.query(models.User).filter(models.User.id == emp_id).first()
    if not emp:
        raise HTTPException(404, "Not found")
    return emp


@app.post("/api/employees", response_model=schemas.EmployeeOut)
def create_employee(data: schemas.EmployeeCreate, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role != "hr_admin":
        raise HTTPException(403, "Only HR Admin can add employees")
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(models.User).filter(models.User.employee_id == data.employee_id).first():
        raise HTTPException(400, "Employee ID already exists")
    emp = models.User(
        employee_id=data.employee_id,
        name=data.name,
        email=data.email,
        password_hash=auth.hash_password(data.password),
        role="employee",
        department=data.department,
        designation=data.designation,
        phone=data.phone,
        address=data.address,
        joining_date=data.joining_date or date.today(),
        basic_salary=data.basic_salary,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@app.put("/api/employees/{emp_id}", response_model=schemas.EmployeeOut)
def update_employee(emp_id: int, data: schemas.EmployeeUpdate,
                    db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role != "hr_admin":
        raise HTTPException(403, "Forbidden")
    emp = db.query(models.User).filter(models.User.id == emp_id).first()
    if not emp:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(emp, k, v)
    db.commit()
    db.refresh(emp)
    return emp


@app.delete("/api/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role != "hr_admin":
        raise HTTPException(403, "Forbidden")
    emp = db.query(models.User).filter(models.User.id == emp_id).first()
    if not emp:
        raise HTTPException(404, "Not found")
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted"}


# ── Resume ──────────────────────────────────────────
@app.post("/api/employees/{emp_id}/resume")
async def upload_resume(emp_id: int, file: UploadFile = File(...),
                         db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role != "hr_admin":
        raise HTTPException(403, "Forbidden")
    os.makedirs("uploads/resumes", exist_ok=True)
    filename = f"{emp_id}_{file.filename}"
    path = f"uploads/resumes/{filename}"
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    r = models.Resume(user_id=emp_id, filename=filename, file_path=path)
    db.add(r)
    db.commit()
    return {"message": "Resume uploaded", "filename": filename}


@app.get("/api/employees/{emp_id}/resume")
def download_resume(emp_id: int, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role not in ["ceo", "hr_admin"] and me.id != emp_id:
        raise HTTPException(403)
    r = db.query(models.Resume).filter(models.Resume.user_id == emp_id).order_by(models.Resume.id.desc()).first()
    if not r:
        raise HTTPException(404, "No resume found")
    return FileResponse(r.file_path, filename=r.filename,
                        media_type="application/octet-stream")


@app.get("/api/employees/{emp_id}/resume/info")
def resume_info(emp_id: int, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    r = db.query(models.Resume).filter(models.Resume.user_id == emp_id).order_by(models.Resume.id.desc()).first()
    if not r:
        return {"has_resume": False}
    return {"has_resume": True, "filename": r.filename, "uploaded_on": str(r.uploaded_on)}


# ══════════════════════════════════════════════════════
#  ATTENDANCE
# ══════════════════════════════════════════════════════
@app.post("/api/attendance/checkin")
def check_in(loc: schemas.AttendanceLocation, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    dist = utils.haversine(OFFICE_LAT, OFFICE_LNG, loc.latitude, loc.longitude)
    if dist > GEOFENCE_RADIUS_M:
        raise HTTPException(400, f"You are {int(dist)}m away from office. Must be within {GEOFENCE_RADIUS_M}m.")
    today = date.today()
    existing = db.query(models.Attendance).filter(
        models.Attendance.user_id == me.id, models.Attendance.date == today).first()
    if existing and existing.check_in:
        raise HTTPException(400, "Already checked in today")
    att = existing or models.Attendance(user_id=me.id, date=today)
    att.check_in = datetime.now()
    att.latitude = loc.latitude
    att.longitude = loc.longitude
    att.status = "present"
    if not existing:
        db.add(att)
    db.commit()
    return {"message": "Checked in successfully", "time": att.check_in.strftime("%H:%M:%S"),
            "distance_m": round(dist)}


@app.post("/api/attendance/checkout")
def check_out(loc: schemas.AttendanceLocation, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    dist = utils.haversine(OFFICE_LAT, OFFICE_LNG, loc.latitude, loc.longitude)
    if dist > GEOFENCE_RADIUS_M:
        raise HTTPException(400, f"You are {int(dist)}m from office. Must be within {GEOFENCE_RADIUS_M}m.")
    today = date.today()
    att = db.query(models.Attendance).filter(
        models.Attendance.user_id == me.id, models.Attendance.date == today).first()
    if not att or not att.check_in:
        raise HTTPException(400, "Not checked in yet today")
    if att.check_out:
        raise HTTPException(400, "Already checked out today")
    att.check_out = datetime.now()
    delta = att.check_out - att.check_in
    att.hours_worked = round(delta.total_seconds() / 3600, 2)
    db.commit()
    return {"message": "Checked out successfully", "hours_worked": att.hours_worked,
            "check_out": att.check_out.strftime("%H:%M:%S")}


@app.get("/api/attendance")
def list_attendance(emp_id: Optional[int] = None,
                     month: Optional[int] = None,
                     year: Optional[int] = None,
                     db: Session = Depends(get_db),
                     me=Depends(auth.get_current_user)):
    q = db.query(models.Attendance)
    if me.role == "employee":
        q = q.filter(models.Attendance.user_id == me.id)
    elif emp_id:
        q = q.filter(models.Attendance.user_id == emp_id)
    records = q.order_by(models.Attendance.date.desc()).all()
    result = []
    for r in records:
        user = db.query(models.User).filter(models.User.id == r.user_id).first()
        result.append({
            "id": r.id, "user_id": r.user_id,
            "employee_name": user.name if user else "",
            "employee_id": user.employee_id if user else "",
            "date": str(r.date),
            "check_in": r.check_in.strftime("%H:%M:%S") if r.check_in else None,
            "check_out": r.check_out.strftime("%H:%M:%S") if r.check_out else None,
            "hours_worked": r.hours_worked,
            "status": r.status,
        })
    return result


# ══════════════════════════════════════════════════════
#  LEAVES
# ══════════════════════════════════════════════════════
@app.post("/api/leaves")
def apply_leave(data: schemas.LeaveCreate, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    leave = models.Leave(
        user_id=me.id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return {"message": "Leave applied", "id": leave.id}


@app.get("/api/leaves")
def list_leaves(db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    q = db.query(models.Leave)
    if me.role == "employee":
        q = q.filter(models.Leave.user_id == me.id)
    leaves = q.order_by(models.Leave.applied_on.desc()).all()
    result = []
    for l in leaves:
        user = db.query(models.User).filter(models.User.id == l.user_id).first()
        result.append({
            "id": l.id, "user_id": l.user_id,
            "employee_name": user.name if user else "",
            "employee_id": user.employee_id if user else "",
            "leave_type": l.leave_type,
            "start_date": str(l.start_date),
            "end_date": str(l.end_date),
            "reason": l.reason,
            "status": l.status,
            "applied_on": l.applied_on.strftime("%d %b %Y") if l.applied_on else "",
        })
    return result


@app.put("/api/leaves/{leave_id}")
def update_leave(leave_id: int, data: schemas.LeaveUpdate,
                  db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role not in ["hr_admin", "ceo"]:
        raise HTTPException(403)
    leave = db.query(models.Leave).filter(models.Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(404)
    leave.status = data.status
    leave.approved_by = me.id
    db.commit()
    return {"message": f"Leave {data.status}"}


# ══════════════════════════════════════════════════════
#  PAYSLIPS
# ══════════════════════════════════════════════════════
@app.post("/api/payslips/generate")
def generate_payslip(data: schemas.PayslipGenerate,
                      db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role not in ["hr_admin", "ceo"]:
        raise HTTPException(403)
    emp = db.query(models.User).filter(models.User.id == data.employee_id).first()
    if not emp:
        raise HTTPException(404, "Employee not found")
    # Check duplicate
    existing = db.query(models.Payslip).filter(
        models.Payslip.user_id == data.employee_id,
        models.Payslip.month == data.month,
        models.Payslip.year == data.year).first()
    if existing:
        raise HTTPException(400, "Payslip already generated for this month")

    basic = emp.basic_salary or 0
    hra = basic * 0.40
    ta = basic * 0.10
    da = basic * 0.15
    pf = basic * 0.12
    tax = basic * 0.05
    net = basic + hra + ta + da - pf - tax

    pdf_path = utils.generate_payslip_pdf(emp, data.month, data.year,
                                           basic, hra, ta, da, pf, tax, net)
    ps = models.Payslip(user_id=data.employee_id, month=data.month, year=data.year,
                         basic_salary=basic, hra=hra, travel_allowance=ta, da=da,
                         pf_deduction=pf, tax_deduction=tax, net_salary=net,
                         pdf_path=pdf_path)
    db.add(ps)
    db.commit()
    db.refresh(ps)
    return {"message": "Payslip generated", "id": ps.id, "net_salary": net}


@app.get("/api/payslips")
def list_payslips(db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    q = db.query(models.Payslip)
    if me.role == "employee":
        q = q.filter(models.Payslip.user_id == me.id)
    payslips = q.order_by(models.Payslip.year.desc(), models.Payslip.month.desc()).all()
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    result = []
    for p in payslips:
        user = db.query(models.User).filter(models.User.id == p.user_id).first()
        result.append({
            "id": p.id, "user_id": p.user_id,
            "employee_name": user.name if user else "",
            "employee_id": user.employee_id if user else "",
            "month": p.month, "year": p.year,
            "month_name": months[p.month - 1] if 1 <= p.month <= 12 else "",
            "basic_salary": p.basic_salary, "net_salary": p.net_salary,
            "generated_on": p.generated_on.strftime("%d %b %Y") if p.generated_on else "",
        })
    return result


@app.get("/api/payslips/{payslip_id}/download")
def download_payslip(payslip_id: int, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    ps = db.query(models.Payslip).filter(models.Payslip.id == payslip_id).first()
    if not ps:
        raise HTTPException(404)
    if me.role == "employee" and ps.user_id != me.id:
        raise HTTPException(403)
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    fname = f"Payslip_{months[ps.month-1]}_{ps.year}.pdf"
    return FileResponse(ps.pdf_path, media_type="application/pdf", filename=fname)


@app.post("/api/payslips/{payslip_id}/email")
def email_payslip(payslip_id: int, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    ps = db.query(models.Payslip).filter(models.Payslip.id == payslip_id).first()
    if not ps:
        raise HTTPException(404)
    if me.role == "employee" and ps.user_id != me.id:
        raise HTTPException(403)
    emp = db.query(models.User).filter(models.User.id == ps.user_id).first()
    try:
        utils.send_payslip_email(emp.email, emp.name, ps)
        return {"message": f"Payslip sent to {emp.email}"}
    except Exception as e:
        raise HTTPException(500, f"Email failed: {str(e)}. Configure SMTP in .env")


# ══════════════════════════════════════════════════════
#  RECRUITMENT
# ══════════════════════════════════════════════════════
@app.get("/api/recruitment")
def list_recruitment(db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    jobs = db.query(models.Recruitment).order_by(models.Recruitment.posted_on.desc()).all()
    return [{"id": j.id, "position": j.position, "department": j.department,
             "description": j.description, "vacancies": j.vacancies,
             "status": j.status, "posted_on": j.posted_on.strftime("%d %b %Y")} for j in jobs]


@app.post("/api/recruitment")
def create_job(data: schemas.RecruitmentCreate, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role not in ["hr_admin", "ceo"]:
        raise HTTPException(403)
    job = models.Recruitment(position=data.position, department=data.department,
                              description=data.description, vacancies=data.vacancies,
                              posted_by=me.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"message": "Job posted", "id": job.id}


@app.put("/api/recruitment/{job_id}")
def update_job(job_id: int, status: str, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role not in ["hr_admin", "ceo"]:
        raise HTTPException(403)
    job = db.query(models.Recruitment).filter(models.Recruitment.id == job_id).first()
    if not job:
        raise HTTPException(404)
    job.status = status
    db.commit()
    return {"message": "Updated"}


@app.delete("/api/recruitment/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), me=Depends(auth.get_current_user)):
    if me.role not in ["hr_admin", "ceo"]:
        raise HTTPException(403)
    job = db.query(models.Recruitment).filter(models.Recruitment.id == job_id).first()
    if not job:
        raise HTTPException(404)
    db.delete(job)
    db.commit()
    return {"message": "Deleted"}


# ══════════════════════════════════════════════════════
#  STATIC FRONTEND
# ══════════════════════════════════════════════════════
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str = ""):
    if full_path.startswith("api"):
        raise HTTPException(404)
    return FileResponse("static/index.html")
