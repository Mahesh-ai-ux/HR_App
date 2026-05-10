# 🏢 Nexila HR Management Portal

> **Full-stack internal HR system for Nexila Technologies, West Tambaram, Chennai.**
> Built with FastAPI + SQLite + Vanilla JS. Production-ready, self-hosted.

---

## ✨ Features

| Feature | CEO | HR Admin | Employee |
|---|---|---|---|
| Dashboard & Stats | ✅ | ✅ | ✅ |
| View All Employees | ✅ | ✅ | — |
| Add / Edit / Delete Employees | — | ✅ | — |
| Upload Employee Resumes | — | ✅ | — |
| Post / Manage Job Openings | ✅ | ✅ | — |
| Geofenced Attendance (Check In/Out) | — | — | ✅ |
| View All Attendance Records | ✅ | ✅ | Own only |
| Apply for Leave | — | — | ✅ |
| Approve / Reject Leaves | ✅ | ✅ | — |
| Generate Payslips (PDF) | ✅ | ✅ | — |
| Download Payslips | ✅ | ✅ | Own only |
| Email Payslip to Employee | ✅ | ✅ | Own only |
| My Profile View | — | — | ✅ |

---

## 🗺️ Geofence

Employees can only check in/out when physically at the office:
- 📍 **Nexila Technologies, West Tambaram, Chennai**
- Coordinates: `12.9291° N, 80.1003° E`
- Radius: `500 metres` (configurable in `.env`)

---

## 🚀 Quick Start

### Option 1 — Shell Script (Recommended)

```bash
# Clone / extract the project
cd nexila-hr

# Linux / macOS
chmod +x start.sh
./start.sh

# Windows
start.bat
```

Open **http://localhost:8000** in your browser.

---

### Option 2 — Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your SMTP credentials

# 4. Run
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Option 3 — Docker

```bash
docker compose up -d
```

---

## 🔑 Default Login Credentials

| Role | Email | Password |
|---|---|---|
| CEO | ceo@nexila.com | ceo123 |
| HR Admin | hr@nexila.com | hr123 |
| Employee 1 | arjun@nexila.com | emp123 |
| Employee 2 | divya@nexila.com | emp456 |

> ⚠️ **Change all passwords immediately after first login in production.**

---

## 📧 Email Setup (Payslip Delivery)

1. Go to your Google Account → **Security** → **App Passwords**
2. Generate an app password for "Mail"
3. Add to `.env`:

```env
SMTP_USER=your_hr_email@gmail.com
SMTP_PASS=your_16_char_app_password
```

---

## 🏗️ Project Structure

```
nexila-hr/
├── main.py              ← FastAPI app + all API routes
├── models.py            ← SQLAlchemy database models
├── schemas.py           ← Pydantic request/response schemas
├── auth.py              ← JWT authentication + password hashing
├── database.py          ← DB engine + session factory
├── utils.py             ← Payslip PDF generator + email sender
├── requirements.txt     ← Python dependencies
├── static/
│   └── index.html       ← Complete SPA frontend (no framework)
├── uploads/
│   ├── resumes/         ← Employee resume files
│   └── payslips/        ← Generated payslip PDFs
├── .env.example         ← Environment variable template
├── Dockerfile           ← Container definition
├── docker-compose.yml   ← Multi-service orchestration
├── nginx.conf           ← Reverse proxy config
├── nexila-hr.service    ← Systemd service (Linux production)
├── start.sh             ← One-click start (Linux/Mac)
└── start.bat            ← One-click start (Windows)
```

---

## 🌐 API Reference

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/auth/login` | Public | Login |
| GET | `/api/dashboard/stats` | All | Dashboard stats |
| GET | `/api/employees` | CEO, HR | List employees |
| POST | `/api/employees` | HR | Add employee |
| PUT | `/api/employees/{id}` | HR | Edit employee |
| DELETE | `/api/employees/{id}` | HR | Delete employee |
| POST | `/api/employees/{id}/resume` | HR | Upload resume |
| GET | `/api/employees/{id}/resume` | HR + Owner | Download resume |
| POST | `/api/attendance/checkin` | Employee | Geofenced check-in |
| POST | `/api/attendance/checkout` | Employee | Geofenced check-out |
| GET | `/api/attendance` | All | Attendance records |
| POST | `/api/leaves` | Employee | Apply leave |
| GET | `/api/leaves` | All | Leave records |
| PUT | `/api/leaves/{id}` | HR, CEO | Approve/Reject |
| POST | `/api/payslips/generate` | HR, CEO | Generate payslip PDF |
| GET | `/api/payslips` | All | List payslips |
| GET | `/api/payslips/{id}/download` | All | Download PDF |
| POST | `/api/payslips/{id}/email` | All | Email payslip |
| GET | `/api/recruitment` | All | Job openings |
| POST | `/api/recruitment` | HR, CEO | Post job |
| DELETE | `/api/recruitment/{id}` | HR, CEO | Remove job |

Interactive docs: **http://localhost:8000/docs**

---

## 🖥️ Production Deployment (Linux VPS)

```bash
# 1. Copy files to server
scp -r nexila-hr/ user@yourserver:/opt/nexila-hr

# 2. Install & setup
cd /opt/nexila-hr
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env   # fill in real values

# 3. Install as system service
sudo cp nexila-hr.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nexila-hr
sudo systemctl start nexila-hr

# 4. Setup Nginx reverse proxy
sudo cp nginx.conf /etc/nginx/sites-available/nexila-hr
sudo ln -s /etc/nginx/sites-available/nexila-hr /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 5. SSL (Let's Encrypt)
sudo certbot --nginx -d your-domain.com
```

---

## 🗄️ Database

- **Development**: SQLite (`nexila_hr.db`) — zero configuration
- **Production**: Switch to PostgreSQL by updating `DATABASE_URL` in `.env`:
  ```
  DATABASE_URL=postgresql://user:pass@localhost:5432/nexila_hr
  pip install psycopg2-binary
  ```

---

## 🔒 Security Notes

- JWT tokens expire per session (no persistence)
- All routes require `Authorization: Bearer <token>` header
- Role-based access enforced server-side on every endpoint
- Geofence validated server-side (not just frontend)
- Passwords hashed with bcrypt

---

## 📞 Support

**Nexila Technologies** — West Tambaram, Chennai, Tamil Nadu 600045  
HR Department: hr@nexila.com
