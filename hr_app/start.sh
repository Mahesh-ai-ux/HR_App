#!/usr/bin/env bash
# ─────────────────────────────────────────────────────
#  Nexila HR — Start Script (Linux / macOS)
# ─────────────────────────────────────────────────────
set -e

echo ""
echo "  ███╗   ██╗███████╗██╗  ██╗██╗██╗      █████╗ "
echo "  ████╗  ██║██╔════╝╚██╗██╔╝██║██║     ██╔══██╗"
echo "  ██╔██╗ ██║█████╗   ╚███╔╝ ██║██║     ███████║"
echo "  ██║╚██╗██║██╔══╝   ██╔██╗ ██║██║     ██╔══██║"
echo "  ██║ ╚████║███████╗██╔╝ ██╗██║███████╗██║  ██║"
echo "  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝"
echo "  HR Management Portal — West Tambaram, Chennai"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found. Install Python 3.10+ first."
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Copy .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from template — edit it to configure SMTP and other settings."
fi

# Create upload directories
mkdir -p uploads/resumes uploads/payslips

# Start
echo ""
echo "Starting Nexila HR on http://0.0.0.0:8000"
echo "Press Ctrl+C to stop"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
