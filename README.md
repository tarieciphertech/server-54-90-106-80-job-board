# JobBoard - Flask Job Advertisement Platform

A complete job advertisement platform built with Flask where the administrator manages everything.

---

## Features
- Public job listings and candidate profiles
- Employer & job seeker registration
- Payment proof upload system
- Admin confirms payments and activates accounts
- Admin creates job listings from employer requests
- Admin publishes candidate profiles
- Visitor inquiry system ("I'm Interested" button)
- **Instant Email + SMS notifications to admin** on every action

---

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure the App
Open `config.py` and update:
- `MAIL_USERNAME` — your Gmail address
- `MAIL_PASSWORD` — your Gmail App Password (not your login password)
- `ADMIN_EMAIL` — admin's email address
- `ADMIN_PHONE` — admin's phone with country code (e.g. +254700000000)
- `AT_USERNAME` — Africa's Talking username
- `AT_API_KEY` — Africa's Talking API key
- `PAYMENT_DETAILS` — your bank/mobile money details

### 3. Gmail App Password Setup
1. Go to your Google Account → Security
2. Enable 2-Step Verification
3. Go to App Passwords → Generate one for "Mail"
4. Use that password in `MAIL_PASSWORD`

### 4. Africa's Talking Setup
1. Sign up at https://africastalking.com
2. Get your API key and username from the dashboard
3. Test in sandbox mode first (free)

### 5. Run the App
```bash
python run.py
```

Visit: http://localhost:5000

---

## Default Admin Account
- **Email:** admin@jobboard.com
- **Password:** admin1234
- **Change this immediately after first login!**

---

## Project Structure
```
job_board/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # Database models
│   ├── notifications.py     # Email + SMS notifications
│   ├── routes/
│   │   ├── auth.py          # Login & Register
│   │   ├── employer.py      # Employer dashboard
│   │   ├── jobseeker.py     # Job seeker dashboard
│   │   ├── admin.py         # Admin panel
│   │   └── public.py        # Public pages
│   ├── templates/           # HTML pages
│   └── static/uploads/      # Uploaded files
├── config.py                # All settings
├── run.py                   # Entry point
└── requirements.txt
```

---

## Admin Notifications
Admin is notified instantly (Email + SMS) when:
- A new employer registers
- A new job seeker registers
- Anyone uploads payment proof
- An employer submits job details
- A job seeker submits their profile
- A visitor clicks "I'm Interested"
