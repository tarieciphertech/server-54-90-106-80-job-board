# 🚀 JobConnect - AWS EC2 + PostgreSQL Deployment Guide

---

## Step 1: Launch EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**
2. Choose **Ubuntu Server 22.04 LTS**
3. Choose instance type: **t2.micro** (free tier) or **t2.small** (recommended)
4. Configure Security Group — open these ports:
   - Port **22** (SSH) — Your IP only
   - Port **80** (HTTP) — Anywhere
   - Port **443** (HTTPS) — Anywhere
5. Create or use an existing **Key Pair** (.pem file)
6. Launch the instance

---

## Step 2: Connect to Your Server

```bash
# Give your key the right permissions
chmod 400 your-key.pem

# Connect via SSH
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

---

## Step 3: Upload Your Project

From your **local machine**, upload the project:

```bash
# Upload via SCP
scp -i your-key.pem -r job_board/ ubuntu@YOUR_EC2_IP:/home/ubuntu/

# OR use git (if your project is on GitHub)
git clone https://github.com/yourusername/job_board.git /home/ubuntu/job_board
```

---

## Step 4: Run the Deployment Script

```bash
cd /home/ubuntu/job_board
chmod +x deploy.sh
bash deploy.sh
```

---

## Step 5: Fill in Environment Variables

```bash
sudo nano /etc/jobboard.env
```

Fill in all values:

```
SECRET_KEY=generate-a-long-random-string-here
DATABASE_URL=postgresql://jobboard_user:CHANGE_THIS_PASSWORD@localhost/jobboard_db
MAIL_USERNAME=yourapp@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PHONE=+263779562073
AT_USERNAME=your_at_username
AT_API_KEY=your_at_api_key
```

> **Generate a secret key:**
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Step 6: Point Your Domain to EC2

In your domain provider (GoDaddy, Namecheap, etc.):

1. Add an **A Record**:
   - Name: `@`
   - Value: `YOUR_EC2_PUBLIC_IP`
2. Add another **A Record**:
   - Name: `www`
   - Value: `YOUR_EC2_PUBLIC_IP`

Wait 5-15 minutes for DNS to propagate.

---

## Step 7: Update Nginx with Your Domain

```bash
sudo nano /etc/nginx/sites-available/jobboard
```

Replace `your-domain.com` with your actual domain, then:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 8: Get Free SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Follow the prompts — Certbot will automatically configure HTTPS.

---

## Step 9: Start the App

```bash
# Activate venv and initialize database
cd /home/ubuntu/job_board
source venv/bin/activate
export $(cat /etc/jobboard.env | xargs)
python3 -c "from app import create_app; app = create_app()"

# Start the service
sudo systemctl start jobboard
sudo systemctl status jobboard
```

---

## Useful Commands

```bash
# Restart the app
sudo systemctl restart jobboard

# View live logs
sudo journalctl -u jobboard -f

# View error logs
cat /var/log/jobboard/error.log

# Restart nginx
sudo systemctl restart nginx

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Connect to database
sudo -u postgres psql jobboard_db
```

---

## Updating the App

When you make changes to the code:

```bash
cd /home/ubuntu/job_board

# Pull latest changes (if using git)
git pull

# Activate venv and install any new dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart the service
sudo systemctl restart jobboard
```

---

## Default Admin Login

- **URL:** https://your-domain.com/login
- **Email:** admin@jobboard.com
- **Password:** admin1234

> ⚠️ Change this immediately after first login!
