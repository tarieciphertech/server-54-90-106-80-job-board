#!/bin/bash
# ══════════════════════════════════════════════════
#  JobConnect - AWS EC2 Deployment Script
#  Run this on a fresh Ubuntu 22.04 EC2 instance
#  Usage: bash deploy.sh
# ══════════════════════════════════════════════════

set -e  # Stop on any error

echo ""
echo "══════════════════════════════════════════"
echo "   JobConnect - Production Deployment"
echo "══════════════════════════════════════════"
echo ""

# ── 1. Update System ──────────────────────────
echo "▶ Updating system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib certbot python3-certbot-nginx git

# ── 2. Setup PostgreSQL ───────────────────────
echo ""
echo "▶ Setting up PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE jobboard_db;
CREATE USER jobboard_user WITH PASSWORD 'CHANGE_THIS_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE jobboard_db TO jobboard_user;
ALTER DATABASE jobboard_db OWNER TO jobboard_user;
EOF
echo "✅ PostgreSQL ready"

# ── 3. Upload / Clone App ─────────────────────
echo ""
echo "▶ Setting up application directory..."
mkdir -p /home/ubuntu/job_board
# NOTE: Upload your job_board folder here via SCP or git clone
# Example: git clone https://github.com/yourusername/job_board.git /home/ubuntu/job_board

# ── 4. Python Virtual Environment ────────────
echo ""
echo "▶ Creating Python virtual environment..."
cd /home/ubuntu/job_board
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# ── 5. Environment Variables ──────────────────
echo ""
echo "▶ Setting up environment variables..."
sudo cp .env.example /etc/jobboard.env
echo ""
echo "⚠️  IMPORTANT: Edit /etc/jobboard.env with your real values!"
echo "    Run: sudo nano /etc/jobboard.env"
echo ""

# ── 6. Create Upload Directories ─────────────
echo "▶ Creating upload directories..."
mkdir -p /home/ubuntu/job_board/app/static/uploads/resumes
mkdir -p /home/ubuntu/job_board/app/static/uploads/proofs
mkdir -p /var/log/jobboard
sudo chown -R ubuntu:www-data /home/ubuntu/job_board/app/static/uploads
sudo chmod -R 775 /home/ubuntu/job_board/app/static/uploads
echo "✅ Directories ready"

# ── 7. Configure Nginx ────────────────────────
echo ""
echo "▶ Configuring Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/jobboard
sudo ln -sf /etc/nginx/sites-available/jobboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
echo "✅ Nginx configured"

# ── 8. Systemd Service ────────────────────────
echo ""
echo "▶ Setting up Gunicorn service..."
sudo cp jobboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jobboard
echo "✅ Service registered"

# ── 9. Summary ────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
echo "  ✅ Setup Complete!"
echo "══════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "1. Fill in your environment variables:"
echo "   sudo nano /etc/jobboard.env"
echo ""
echo "2. Update nginx.conf with your domain:"
echo "   sudo nano /etc/nginx/sites-available/jobboard"
echo ""
echo "3. Get SSL certificate (replace with your domain):"
echo "   sudo certbot --nginx -d your-domain.com -d www.your-domain.com"
echo ""
echo "4. Start the app:"
echo "   sudo systemctl start jobboard"
echo "   sudo systemctl status jobboard"
echo ""
echo "5. Check logs if something goes wrong:"
echo "   sudo journalctl -u jobboard -f"
echo "   cat /var/log/jobboard/error.log"
echo ""
