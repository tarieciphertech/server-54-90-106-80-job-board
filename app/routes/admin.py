from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app.models import db, User, Payment, JobRequest, JobListing, JobSeekerProfile, Inquiry
from app.notifications import notify_user_activation

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    pending_payments = Payment.query.filter_by(status='pending').count()
    total_users = User.query.filter(User.role != 'admin').count()
    total_listings = JobListing.query.filter_by(is_active=True).count()
    pending_inquiries = Inquiry.query.filter_by(is_handled=False).count()
    recent_payments = Payment.query.filter_by(status='pending').order_by(Payment.submitted_at.desc()).all()
    recent_inquiries = Inquiry.query.filter_by(is_handled=False).order_by(Inquiry.submitted_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           pending_payments=pending_payments,
                           total_users=total_users,
                           total_listings=total_listings,
                           pending_inquiries=pending_inquiries,
                           recent_payments=recent_payments,
                           recent_inquiries=recent_inquiries)


@admin_bp.route('/payments')
@login_required
@admin_required
def payments():
    all_payments = Payment.query.order_by(Payment.submitted_at.desc()).all()
    return render_template('admin/payments.html', payments=all_payments)


@admin_bp.route('/confirm-payment/<int:payment_id>')
@login_required
@admin_required
def confirm_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'confirmed'
    payment.confirmed_at = datetime.utcnow()

    user = User.query.get(payment.user_id)
    user.is_approved = True
    db.session.commit()

    # Notify the user
    notify_user_activation(user)

    flash(f'{user.name} has been activated successfully!', 'success')
    return redirect(url_for('admin_bp.payments'))


@admin_bp.route('/reject-payment/<int:payment_id>')
@login_required
@admin_required
def reject_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'rejected'
    db.session.commit()
    flash('Payment rejected.', 'warning')
    return redirect(url_for('admin_bp.payments'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.filter(User.role != 'admin').order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/job-requests')
@login_required
@admin_required
def job_requests():
    requests = JobRequest.query.order_by(JobRequest.submitted_at.desc()).all()
    return render_template('admin/job_requests.html', requests=requests)


@admin_bp.route('/create-listing/<int:request_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def create_listing(request_id):
    job_request = JobRequest.query.get_or_404(request_id)

    if request.method == 'POST':
        listing = JobListing(
            job_request_id=job_request.id,
            title=request.form.get('title'),
            company_name=request.form.get('company_name'),
            description=request.form.get('description'),
            location=request.form.get('location'),
            salary_range=request.form.get('salary_range'),
            requirements=request.form.get('requirements'),
            is_active=True
        )
        db.session.add(listing)
        db.session.commit()
        flash('Job listing published successfully!', 'success')
        return redirect(url_for('admin_bp.job_requests'))

    return render_template('admin/create_listing.html', job_request=job_request)


@admin_bp.route('/listings')
@login_required
@admin_required
def listings():
    all_listings = JobListing.query.order_by(JobListing.created_at.desc()).all()
    return render_template('admin/listings.html', listings=all_listings)


@admin_bp.route('/toggle-listing/<int:listing_id>')
@login_required
@admin_required
def toggle_listing(listing_id):
    listing = JobListing.query.get_or_404(listing_id)
    listing.is_active = not listing.is_active
    db.session.commit()
    status = 'activated' if listing.is_active else 'deactivated'
    flash(f'Listing {status}.', 'success')
    return redirect(url_for('admin_bp.listings'))


@admin_bp.route('/candidates')
@login_required
@admin_required
def candidates():
    profiles = JobSeekerProfile.query.order_by(JobSeekerProfile.submitted_at.desc()).all()
    return render_template('admin/candidates.html', profiles=profiles)


@admin_bp.route('/publish-candidate/<int:profile_id>')
@login_required
@admin_required
def publish_candidate(profile_id):
    profile = JobSeekerProfile.query.get_or_404(profile_id)
    profile.is_published = not profile.is_published
    db.session.commit()
    status = 'published' if profile.is_published else 'unpublished'
    flash(f'Candidate profile {status}.', 'success')
    return redirect(url_for('admin_bp.candidates'))


@admin_bp.route('/inquiries')
@login_required
@admin_required
def inquiries():
    all_inquiries = Inquiry.query.order_by(Inquiry.submitted_at.desc()).all()
    return render_template('admin/inquiries.html', inquiries=all_inquiries)


@admin_bp.route('/handle-inquiry/<int:inquiry_id>')
@login_required
@admin_required
def handle_inquiry(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    inquiry.is_handled = True
    db.session.commit()
    flash('Inquiry marked as handled.', 'success')
    return redirect(url_for('admin_bp.inquiries'))


@admin_bp.route('/adverts')
@login_required
@admin_required
def adverts():
    from app.models import Advertisement, AdvertPayment
    all_payments = AdvertPayment.query.order_by(AdvertPayment.submitted_at.desc()).all()
    all_adverts = Advertisement.query.order_by(Advertisement.submitted_at.desc()).all()
    return render_template('admin/adverts.html', payments=all_payments, adverts=all_adverts)


@admin_bp.route('/confirm-advert-payment/<int:payment_id>')
@login_required
@admin_required
def confirm_advert_payment(payment_id):
    from app.models import AdvertPayment, AD_PACKAGES
    from datetime import timedelta
    payment = AdvertPayment.query.get_or_404(payment_id)
    payment.status = 'confirmed'
    payment.confirmed_at = datetime.utcnow()
    user = User.query.get(payment.user_id)
    user.is_approved = True
    db.session.commit()
    notify_user_activation(user)
    flash(f'{user.name} advert payment confirmed!', 'success')
    return redirect(url_for('admin_bp.adverts'))


@admin_bp.route('/publish-advert/<int:advert_id>')
@login_required
@admin_required
def publish_advert(advert_id):
    from app.models import Advertisement, AdvertPayment, AD_PACKAGES
    from datetime import timedelta
    advert = Advertisement.query.get_or_404(advert_id)
    payment = AdvertPayment.query.filter_by(user_id=advert.user_id, status='confirmed').first()
    if not advert.is_published:
        advert.is_published = True
        days = AD_PACKAGES.get(advert.package, {}).get('days', 90)
        advert.expires_at = datetime.utcnow() + timedelta(days=days)
        db.session.commit()
        flash(f'Advert published! Expires in {days} days.', 'success')
    else:
        advert.is_published = False
        db.session.commit()
        flash('Advert unpublished.', 'warning')
    return redirect(url_for('admin_bp.adverts'))


@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def profile():
    return render_template('admin/profile.html')


@admin_bp.route('/change-password', methods=['POST'])
@login_required
@admin_required
def change_password():
    from werkzeug.security import check_password_hash, generate_password_hash
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('admin_bp.profile'))

    if len(new_password) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('admin_bp.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('admin_bp.profile'))

    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash('✅ Password changed successfully!', 'success')
    return redirect(url_for('admin_bp.profile'))


@admin_bp.route('/change-email', methods=['POST'])
@login_required
@admin_required
def change_email():
    from werkzeug.security import check_password_hash
    password = request.form.get('password')
    new_email = request.form.get('new_email')

    if not check_password_hash(current_user.password, password):
        flash('Password is incorrect.', 'danger')
        return redirect(url_for('admin_bp.profile'))

    if User.query.filter_by(email=new_email).first():
        flash('That email is already in use.', 'danger')
        return redirect(url_for('admin_bp.profile'))

    current_user.email = new_email
    db.session.commit()
    flash('✅ Email updated successfully!', 'success')
    return redirect(url_for('admin_bp.profile'))
