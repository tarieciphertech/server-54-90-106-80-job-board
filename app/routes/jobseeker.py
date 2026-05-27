from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Payment, JobSeekerProfile
from app.notifications import notify_payment_proof, notify_profile_submitted
import os

jobseeker = Blueprint('jobseeker', __name__, url_prefix='/jobseeker')


def save_file(file, subfolder):
    filename = secure_filename(file.filename)
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    file.save(path)
    return os.path.join(subfolder, filename)


@jobseeker.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'jobseeker':
        return redirect(url_for('public.home'))
    payment = Payment.query.filter_by(user_id=current_user.id).first()
    profile = JobSeekerProfile.query.filter_by(user_id=current_user.id).first()
    return render_template('jobseeker/dashboard.html',
                           payment=payment,
                           profile=profile,
                           payment_details=current_app.config['PAYMENT_DETAILS'])


@jobseeker.route('/upload-proof', methods=['POST'])
@login_required
def upload_proof():
    if current_user.role != 'jobseeker':
        return redirect(url_for('public.home'))

    file = request.files.get('proof')
    if not file or file.filename == '':
        flash('Please select a file.', 'danger')
        return redirect(url_for('jobseeker.dashboard'))

    filepath = save_file(file, 'proofs')
    existing = Payment.query.filter_by(user_id=current_user.id).first()
    if existing:
        existing.proof_file = filepath
        existing.status = 'pending'
    else:
        payment = Payment(user_id=current_user.id, proof_file=filepath)
        db.session.add(payment)

    db.session.commit()

    # Notify admin instantly
    notify_payment_proof(current_user)

    flash('Payment proof uploaded! The admin will confirm shortly.', 'success')
    return redirect(url_for('jobseeker.dashboard'))


@jobseeker.route('/submit-profile', methods=['POST'])
@login_required
def submit_profile():
    if current_user.role != 'jobseeker':
        return redirect(url_for('public.home'))

    if not current_user.is_approved:
        flash('Your account must be activated before submitting your profile.', 'warning')
        return redirect(url_for('jobseeker.dashboard'))

    resume_file = request.files.get('resume')
    resume_path = None
    if resume_file and resume_file.filename != '':
        resume_path = save_file(resume_file, 'resumes')

    existing = JobSeekerProfile.query.filter_by(user_id=current_user.id).first()
    if existing:
        existing.full_name = request.form.get('full_name')
        existing.skills = request.form.get('skills')
        existing.experience = request.form.get('experience')
        existing.education = request.form.get('education')
        if resume_path:
            existing.resume_file = resume_path
    else:
        profile = JobSeekerProfile(
            user_id=current_user.id,
            full_name=request.form.get('full_name'),
            skills=request.form.get('skills'),
            experience=request.form.get('experience'),
            education=request.form.get('education'),
            resume_file=resume_path
        )
        db.session.add(profile)

    db.session.commit()

    # Notify admin instantly
    notify_profile_submitted(current_user)

    flash('Profile submitted! Admin will review and publish it shortly.', 'success')
    return redirect(url_for('jobseeker.dashboard'))
