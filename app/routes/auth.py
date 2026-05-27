from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User
from app.notifications import notify_new_employer, notify_new_jobseeker, notify_new_advertiser
from app.security import limiter, sanitize

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def register():
    if request.method == 'POST':
        name = sanitize(request.form.get('name'))
        email = sanitize(request.form.get('email'))
        phone = sanitize(request.form.get('phone'))
        password = request.form.get('password')
        role = request.form.get('role')

        if role not in ['employer', 'jobseeker', 'advertiser']:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('auth.register'))

        # Job seekers are auto-approved (free registration)
        is_approved = True if role == 'jobseeker' else False

        user = User(
            name=name, email=email, phone=phone,
            password=generate_password_hash(password),
            role=role,
            is_approved=is_approved
        )
        db.session.add(user)
        db.session.commit()

        if role == 'employer':
            notify_new_employer(user)
        elif role == 'jobseeker':
            notify_new_jobseeker(user)
        elif role == 'advertiser':
            notify_new_advertiser(user)

        if role == 'jobseeker':
            flash('Welcome to JobConnect! Your account is active. Complete your profile below.', 'success')
        else:
            flash('Registration successful! Please upload your payment proof to proceed.', 'success')

        login_user(user)

        if role == 'employer':
            return redirect(url_for('employer.dashboard'))
        elif role == 'advertiser':
            return redirect(url_for('advertiser.dashboard'))
        else:
            return redirect(url_for('jobseeker.dashboard'))

    return render_template('auth/register.html')


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        email = sanitize(request.form.get('email'))
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user)

        if user.role == 'admin':
            return redirect(url_for('admin_bp.dashboard'))
        elif user.role == 'employer':
            return redirect(url_for('employer.dashboard'))
        elif user.role == 'advertiser':
            return redirect(url_for('advertiser.dashboard'))
        else:
            return redirect(url_for('jobseeker.dashboard'))

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('public.home'))
