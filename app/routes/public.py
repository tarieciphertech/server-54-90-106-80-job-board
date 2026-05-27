from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import db, JobListing, JobSeekerProfile, Inquiry, Advertisement
from app.notifications import notify_new_inquiry
from datetime import datetime

public = Blueprint('public', __name__)


@public.route('/')
def home():
    latest_jobs = JobListing.query.filter_by(is_active=True).order_by(JobListing.created_at.desc()).limit(6).all()
    latest_candidates = JobSeekerProfile.query.filter_by(is_published=True).order_by(JobSeekerProfile.submitted_at.desc()).limit(6).all()
    active_adverts = Advertisement.query.filter_by(is_published=True).filter(
        Advertisement.expires_at > datetime.utcnow()
    ).order_by(Advertisement.submitted_at.desc()).all()
    return render_template('public/home.html',
                           latest_jobs=latest_jobs,
                           latest_candidates=latest_candidates,
                           active_adverts=active_adverts)


@public.route('/jobs')
def jobs():
    all_jobs = JobListing.query.filter_by(is_active=True).order_by(JobListing.created_at.desc()).all()
    return render_template('public/jobs.html', jobs=all_jobs)


@public.route('/jobs/<int:job_id>')
def job_detail(job_id):
    job = JobListing.query.get_or_404(job_id)
    return render_template('public/job_detail.html', job=job)


@public.route('/candidates')
def candidates():
    all_candidates = JobSeekerProfile.query.filter_by(is_published=True).order_by(JobSeekerProfile.submitted_at.desc()).all()
    return render_template('public/candidates.html', candidates=all_candidates)


@public.route('/candidates/<int:profile_id>')
def candidate_detail(profile_id):
    candidate = JobSeekerProfile.query.get_or_404(profile_id)
    return render_template('public/candidate_detail.html', candidate=candidate)


@public.route('/adverts')
def adverts():
    active_adverts = Advertisement.query.filter_by(is_published=True).filter(
        Advertisement.expires_at > datetime.utcnow()
    ).order_by(Advertisement.submitted_at.desc()).all()
    return render_template('public/adverts.html', adverts=active_adverts)


@public.route('/inquire', methods=['POST'])
def inquire():
    inquiry = Inquiry(
        visitor_name=request.form.get('visitor_name'),
        visitor_email=request.form.get('visitor_email'),
        visitor_phone=request.form.get('visitor_phone'),
        inquiry_type=request.form.get('inquiry_type'),
        reference_id=request.form.get('reference_id'),
        message=request.form.get('message')
    )
    db.session.add(inquiry)
    db.session.commit()

    reference_title = ''
    if inquiry.inquiry_type == 'job':
        job = JobListing.query.get(inquiry.reference_id)
        reference_title = job.title if job else 'a job listing'
    else:
        candidate = JobSeekerProfile.query.get(inquiry.reference_id)
        reference_title = candidate.full_name if candidate else 'a candidate'

    notify_new_inquiry(inquiry, reference_title)
    flash('Your inquiry has been sent! The administrator will contact you shortly.', 'success')
    return redirect(request.referrer or url_for('public.home'))


@public.route('/contact')
def contact():
    return render_template('public/contact.html')


@public.route('/uploads/<path:filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    import os
    upload_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'static', 'uploads'
    )
    return send_from_directory(upload_folder, filename)
