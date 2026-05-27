from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'jobseeker', 'employer', 'admin'
    is_approved = db.Column(db.Boolean, default=False)  # Activated by admin after payment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payment = db.relationship('Payment', backref='user', uselist=False)
    job_request = db.relationship('JobRequest', backref='employer', uselist=False)
    profile = db.relationship('JobSeekerProfile', backref='user', uselist=False)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    proof_file = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending / confirmed / rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)


class JobRequest(db.Model):
    """Submitted by employer — admin turns this into a real listing"""
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    company_name = db.Column(db.String(200))
    job_title = db.Column(db.String(200))
    job_description = db.Column(db.Text)
    location = db.Column(db.String(100))
    salary_range = db.Column(db.String(100))
    requirements = db.Column(db.Text)
    additional_notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class JobListing(db.Model):
    """Created by Admin — shown publicly on the site"""
    id = db.Column(db.Integer, primary_key=True)
    job_request_id = db.Column(db.Integer, db.ForeignKey('job_request.id'), nullable=True)
    title = db.Column(db.String(200))
    company_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    salary_range = db.Column(db.String(100))
    requirements = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class JobSeekerProfile(db.Model):
    """Submitted by job seeker — published by admin"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    full_name = db.Column(db.String(100))
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)
    education = db.Column(db.Text)
    resume_file = db.Column(db.String(200))
    is_published = db.Column(db.Boolean, default=False)  # Published by admin
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class Inquiry(db.Model):
    """When a visitor clicks 'I am Interested' — admin is notified"""
    id = db.Column(db.Integer, primary_key=True)
    visitor_name = db.Column(db.String(100))
    visitor_email = db.Column(db.String(120))
    visitor_phone = db.Column(db.String(20))
    inquiry_type = db.Column(db.String(20))  # 'job' or 'candidate'
    reference_id = db.Column(db.Integer)     # JobListing id or JobSeekerProfile id
    message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_handled = db.Column(db.Boolean, default=False)


# ── Advertiser Packages ──────────────────────────────────────────────
AD_PACKAGES = {
    '3months':  {'label': '3 Months',  'price': 50,  'days': 90},
    '6months':  {'label': '6 Months',  'price': 70,  'days': 180},
    '12months': {'label': '12 Months', 'price': 100, 'days': 365},
}


class AdvertPayment(db.Model):
    """Payment proof submitted by advertiser"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    package = db.Column(db.String(20))
    proof_file = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', backref='advert_payment', foreign_keys=[user_id])


class Advertisement(db.Model):
    """Ad submitted by advertiser — published by admin"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    business_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    contact_info = db.Column(db.String(200))
    website_url = db.Column(db.String(300), nullable=True)
    image_file = db.Column(db.String(200), nullable=True)
    package = db.Column(db.String(20))
    is_published = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='advertisement', foreign_keys=[user_id])

    @property
    def is_expired(self):
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def days_remaining(self):
        if self.expires_at:
            delta = self.expires_at - datetime.utcnow()
            return max(0, delta.days)
        return 0

    @property
    def package_label(self):
        return AD_PACKAGES.get(self.package, {}).get('label', self.package)
