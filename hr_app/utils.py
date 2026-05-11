import math
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime

# ─── Haversine distance ────────────────────────────────────────────────────────
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in metres between two GPS coords."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─── PDF Payslip ───────────────────────────────────────────────────────────────
def generate_payslip_pdf(employee, month: int, year: int,
                          basic: float, hra: float, ta: float, da: float,
                          pf: float, tax: float, net: float) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.graphics.shapes import Drawing, Line

    month_names = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]
    month_name = month_names[month - 1] if 1 <= month <= 12 else str(month)

    # Use absolute path so FileResponse can find it in Docker and locally
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(base_dir, "uploads", "payslips")
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join("uploads", "payslips", f"payslip_{employee.id}_{year}_{month:02d}.pdf")
    abs_path = os.path.join(base_dir, path)

    doc = SimpleDocTemplate(abs_path, pagesize=A4,
                             topMargin=15*mm, bottomMargin=15*mm,
                             leftMargin=20*mm, rightMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle("hdr", fontSize=22, textColor=colors.HexColor("#0A2342"),
                                   spaceAfter=2, alignment=TA_CENTER, fontName="Helvetica-Bold")
    sub_style = ParagraphStyle("sub", fontSize=10, textColor=colors.HexColor("#4A90D9"),
                                spaceAfter=1, alignment=TA_CENTER)
    story.append(Paragraph("NEXILA TECHNOLOGIES", header_style))
    story.append(Paragraph("West Tambaram, Chennai — Tamil Nadu 600045", sub_style))
    story.append(Paragraph(f"SALARY SLIP — {month_name.upper()} {year}", sub_style))
    story.append(Spacer(1, 8*mm))

    # Employee details
    emp_data = [
        ["Employee ID", employee.employee_id or "—", "Department", employee.department or "—"],
        ["Name", employee.name, "Designation", employee.designation or "—"],
        ["Email", employee.email, "Joining Date", str(employee.joining_date or "—")],
    ]
    emp_table = Table(emp_data, colWidths=[35*mm, 60*mm, 35*mm, 60*mm])
    emp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#0A2342")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#0A2342")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 8*mm))

    # Earnings / Deductions
    salary_data = [
        ["EARNINGS", "AMOUNT (₹)", "DEDUCTIONS", "AMOUNT (₹)"],
        ["Basic Salary", f"{basic:,.2f}", "Provident Fund (12%)", f"{pf:,.2f}"],
        ["HRA (40%)", f"{hra:,.2f}", "Income Tax (5%)", f"{tax:,.2f}"],
        ["Travel Allowance (10%)", f"{ta:,.2f}", "", ""],
        ["DA (15%)", f"{da:,.2f}", "", ""],
        ["GROSS EARNINGS", f"{basic+hra+ta+da:,.2f}", "TOTAL DEDUCTIONS", f"{pf+tax:,.2f}"],
    ]
    sal_table = Table(salary_data, colWidths=[65*mm, 30*mm, 65*mm, 30*mm])
    sal_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A2342")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F0FE")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
    ]))
    story.append(sal_table)
    story.append(Spacer(1, 8*mm))

    # Net Salary box
    net_data = [["NET SALARY", f"₹ {net:,.2f}"]]
    net_table = Table(net_data, colWidths=[130*mm, 60*mm])
    net_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0A2342")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(net_table)
    story.append(Spacer(1, 10*mm))

    # Footer
    footer_style = ParagraphStyle("ft", fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Paragraph("This is a computer-generated payslip and does not require a signature.", footer_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}", footer_style))

    doc.build(story)
    return path


# ─── Email ─────────────────────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "your_email@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "your_app_password")


def send_payslip_email(to_email: str, emp_name: str, payslip) -> None:
    month_names = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]
    month_name = month_names[payslip.month - 1]
    subject = f"Your Payslip for {month_name} {payslip.year} — Nexila Technologies"
    body = f"""Dear {emp_name},

Please find attached your salary slip for {month_name} {payslip.year}.

  Net Salary : ₹ {payslip.net_salary:,.2f}
  Basic      : ₹ {payslip.basic_salary:,.2f}
  Month      : {month_name} {payslip.year}

For any queries, please contact HR at hr@nexila.com.

Best Regards,
HR Department
Nexila Technologies
"""
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if payslip.pdf_path and os.path.exists(payslip.pdf_path):
        with open(payslip.pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f'attachment; filename="Payslip_{month_name}_{payslip.year}.pdf"')
            msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
    except Exception as e:
        raise RuntimeError(f"Email failed: {e}")
