from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Payment, JobRequest
from app.notifications import notify_payment_proof, notify_job_request
import os

employer = Blueprint('employer', __name__, url_prefix='/employer')


def save_file(file, subfolder):
    filename = secure_filename(file.filename)
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    file.save(path)
    return os.path.join(subfolder, filename)


@employer.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'employer':
        return redirect(url_for('public.home'))
    payment = Payment.query.filter_by(user_id=current_user.id).first()
    job_request = JobRequest.query.filter_by(employer_id=current_user.id).first()
    return render_template('employer/dashboard.html',
                           payment=payment,
                           job_request=job_request,
                           payment_details=current_app.config['PAYMENT_DETAILS'])


@employer.route('/upload-proof', methods=['POST'])
@login_required
def upload_proof():
    if current_user.role != 'employer':
        return redirect(url_for('public.home'))

    file = request.files.get('proof')
    if not file or file.filename == '':
        flash('Please select a file.', 'danger')
        return redirect(url_for('employer.dashboard'))

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
    return redirect(url_for('employer.dashboard'))


@employer.route('/submit-job', methods=['POST'])
@login_required
def submit_job():
    if current_user.role != 'employer':
        return redirect(url_for('public.home'))

    if not current_user.is_approved:
        flash('Your account must be activated before submitting a job request.', 'warning')
        return redirect(url_for('employer.dashboard'))

    job_request = JobRequest(
        employer_id=current_user.id,
        company_name=request.form.get('company_name'),
        job_title=request.form.get('job_title'),
        job_description=request.form.get('job_description'),
        location=request.form.get('location'),
        salary_range=request.form.get('salary_range'),
        requirements=request.form.get('requirements'),
        additional_notes=request.form.get('additional_notes')
    )
    db.session.add(job_request)
    db.session.commit()

    # Notify admin instantly
    notify_job_request(current_user, job_request)

    flash('Job request submitted! Admin will create your listing shortly.', 'success')
    return redirect(url_for('employer.dashboard'))
