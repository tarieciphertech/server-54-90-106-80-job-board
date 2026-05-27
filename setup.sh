#!/bin/bash
# ══════════════════════════════════════════════════
#  JobConnect - One-Click Setup Script
#  Run: bash setup.sh
# ══════════════════════════════════════════════════

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}     JobConnect - Production Setup        ${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo ""

# ── Collect all info upfront ──────────────────────
echo -e "${YELLOW}Please answer the following questions:${NC}"
echo ""

read -p "📧 Gmail address (for sending notifications): " MAIL_USERNAME
read -s -p "🔑 Gmail App Password (16 chars): " MAIL_PASSWORD
echo ""
read -p "📬 Admin email (where you receive alerts): " ADMIN_EMAIL
read -p "📱 Admin phone (e.g. +263779562073): " ADMIN_PHONE
read -p "📡 Africa's Talking Username: " AT_USERNAME
read -s -p "🔐 Africa's Talking API Key: " AT_API_KEY
echo ""
echo ""
read -p "🏦 Bank Name: " BANK_NAME
read -p "👤 Account Name: " ACCOUNT_NAME
read -p "🔢 Account Number: " ACCOUNT_NUMBER
read -p "📱 Mobile Money Number: " MOBILE_MONEY
read -p "💵 Employer Fee (e.g. \$10): " EMPLOYER_FEE
read -p "💵 Job Seeker Fee (e.g. \$5): " SEEKER_FEE
read -p "🗄️  PostgreSQL password for DB user: " DB_PASSWORD

echo ""
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}  Installing & Configuring Everything...  ${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo ""

# ── Generate secret key ───────────────────────────
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# ── 1. System packages ────────────────────────────
echo -e "${YELLOW}▶ Installing system packages...${NC}"
sudo apt update -qq
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib -qq
echo -e "${GREEN}✅ System packages installed${NC}"

# ── 2. PostgreSQL ─────────────────────────────────
echo ""
echo -e "${YELLOW}▶ Setting up PostgreSQL...${NC}"
sudo systemctl start postgresql
sudo systemctl enable postgresql

sudo -u postgres psql <<EOF 2>/dev/null || true
CREATE DATABASE jobboard_db;
CREATE USER jobboard_user WITH PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE jobboard_db TO jobboard_user;
ALTER DATABASE jobboard_db OWNER TO jobboard_user;
EOF
echo -e "${GREEN}✅ PostgreSQL ready — database: jobboard_db${NC}"

# ── 3. Virtual environment ────────────────────────
echo ""
echo -e "${YELLOW}▶ Setting up Python virtual environment...${NC}"
cd /home/ubuntu/job_board
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✅ Python dependencies installed${NC}"

# ── 4. Environment file ───────────────────────────
echo ""
echo -e "${YELLOW}▶ Writing environment variables...${NC}"
sudo bash -c "cat > /etc/jobboard.env" <<EOF
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql://jobboard_user:${DB_PASSWORD}@localhost/jobboard_db
MAIL_USERNAME=${MAIL_USERNAME}
MAIL_PASSWORD=${MAIL_PASSWORD}
ADMIN_EMAIL=${ADMIN_EMAIL}
ADMIN_PHONE=${ADMIN_PHONE}
AT_USERNAME=${AT_USERNAME}
AT_API_KEY=${AT_API_KEY}
PAYMENT_DETAILS=Bank: ${BANK_NAME} | Account: ${ACCOUNT_NAME} | Number: ${ACCOUNT_NUMBER} | Mobile Money: ${MOBILE_MONEY} | Employer Fee: ${EMPLOYER_FEE} | Job Seeker Fee: ${SEEKER_FEE} | Reference: Your Full Name
EOF
sudo chmod 600 /etc/jobboard.env
echo -e "${GREEN}✅ Environment variables saved to /etc/jobboard.env${NC}"

# ── 5. Upload directories ─────────────────────────
echo ""
echo -e "${YELLOW}▶ Creating upload directories...${NC}"
mkdir -p /home/ubuntu/job_board/app/static/uploads/resumes
mkdir -p /home/ubuntu/job_board/app/static/uploads/proofs
sudo mkdir -p /var/log/jobboard
sudo chown -R ubuntu:www-data /home/ubuntu/job_board/app/static/uploads
sudo chmod -R 775 /home/ubuntu/job_board/app/static/uploads
echo -e "${GREEN}✅ Upload directories ready${NC}"

# ── 6. Initialize database ────────────────────────
echo ""
echo -e "${YELLOW}▶ Initializing database...${NC}"
cd /home/ubuntu/job_board
source venv/bin/activate
export $(sudo cat /etc/jobboard.env | xargs)
python3 -c "from app import create_app; app = create_app(); print('✅ Database tables created')"

# ── 7. Nginx config ───────────────────────────────
echo ""
echo -e "${YELLOW}▶ Configuring Nginx...${NC}"
sudo bash -c "cat > /etc/nginx/sites-available/jobboard" <<'EOF'
server {
    listen 80;
    server_name 54.90.106.80;

    location /static/ {
        alias /home/ubuntu/job_board/app/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 16M;
}
EOF
sudo ln -sf /etc/nginx/sites-available/jobboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
echo -e "${GREEN}✅ Nginx configured${NC}"

# ── 8. Gunicorn systemd service ───────────────────
echo ""
echo -e "${YELLOW}▶ Setting up Gunicorn service...${NC}"
sudo bash -c "cat > /etc/systemd/system/jobboard.service" <<'EOF'
[Unit]
Description=Gunicorn instance for JobConnect
After=network.target postgresql.service

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/job_board
EnvironmentFile=/etc/jobboard.env
ExecStart=/home/ubuntu/job_board/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/jobboard/access.log \
    --error-logfile /var/log/jobboard/error.log \
    wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable jobboard
sudo systemctl start jobboard
echo -e "${GREEN}✅ Gunicorn service started${NC}"

# ── 9. Final check ────────────────────────────────
echo ""
sleep 2
STATUS=$(sudo systemctl is-active jobboard)
if [ "$STATUS" = "active" ]; then
    echo -e "${GREEN}══════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ JobConnect is LIVE!                  ${NC}"
    echo -e "${GREEN}══════════════════════════════════════════${NC}"
    echo ""
    echo -e "  🌐 Visit:     ${BLUE}http://54.90.106.80${NC}"
    echo -e "  👤 Admin:     ${BLUE}http://54.90.106.80/login${NC}"
    echo -e "  📧 Email:     ${BLUE}admin@jobboard.com${NC}"
    echo -e "  🔑 Password:  ${BLUE}admin1234${NC}"
    echo ""
    echo -e "${YELLOW}  ⚠️  Change the admin password after first login!${NC}"
    echo ""
    echo -e "  Useful commands:"
    echo -e "  ${BLUE}sudo systemctl restart jobboard${NC}   — Restart app"
    echo -e "  ${BLUE}sudo journalctl -u jobboard -f${NC}    — View live logs"
    echo -e "  ${BLUE}sudo systemctl status jobboard${NC}    — Check status"
    echo ""
else
    echo -e "${RED}══════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ Something went wrong!                ${NC}"
    echo -e "${RED}══════════════════════════════════════════${NC}"
    echo ""
    echo "Check the logs:"
    echo "  sudo journalctl -u jobboard -f"
    echo "  cat /var/log/jobboard/error.log"
fi
