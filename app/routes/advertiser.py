from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, AdvertPayment, Advertisement, AD_PACKAGES
from app.notifications import notify_new_advertiser, notify_advert_payment, notify_advert_submitted
import os

advertiser = Blueprint('advertiser', __name__, url_prefix='/advertiser')


def save_file(file, subfolder):
    filename = secure_filename(file.filename)
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    file.save(path)
    return os.path.join(subfolder, filename)


@advertiser.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'advertiser':
        return redirect(url_for('public.home'))
    payment = AdvertPayment.query.filter_by(user_id=current_user.id).first()
    advert = Advertisement.query.filter_by(user_id=current_user.id).first()
    return render_template('advertiser/dashboard.html',
                           payment=payment,
                           advert=advert,
                           packages=AD_PACKAGES,
                           payment_details=current_app.config['PAYMENT_DETAILS'])


@advertiser.route('/upload-proof', methods=['POST'])
@login_required
def upload_proof():
    if current_user.role != 'advertiser':
        return redirect(url_for('public.home'))

    file = request.files.get('proof')
    package = request.form.get('package')

    if not file or file.filename == '':
        flash('Please select a payment proof file.', 'danger')
        return redirect(url_for('advertiser.dashboard'))

    if package not in AD_PACKAGES:
        flash('Please select a valid package.', 'danger')
        return redirect(url_for('advertiser.dashboard'))

    filepath = save_file(file, 'proofs')
    existing = AdvertPayment.query.filter_by(user_id=current_user.id).first()
    if existing:
        existing.proof_file = filepath
        existing.package = package
        existing.status = 'pending'
    else:
        payment = AdvertPayment(
            user_id=current_user.id,
            package=package,
            proof_file=filepath
        )
        db.session.add(payment)

    db.session.commit()
    notify_advert_payment(current_user, package)
    flash('Payment proof uploaded! Admin will confirm shortly.', 'success')
    return redirect(url_for('advertiser.dashboard'))


@advertiser.route('/submit-advert', methods=['POST'])
@login_required
def submit_advert():
    if current_user.role != 'advertiser':
        return redirect(url_for('public.home'))

    if not current_user.is_approved:
        flash('Your account must be activated before submitting an advert.', 'warning')
        return redirect(url_for('advertiser.dashboard'))

    image_file = request.files.get('image')
    image_path = None
    if image_file and image_file.filename != '':
        image_path = save_file(image_file, 'adverts')

    existing = Advertisement.query.filter_by(user_id=current_user.id).first()
    if existing:
        existing.business_name = request.form.get('business_name')
        existing.description = request.form.get('description')
        existing.contact_info = request.form.get('contact_info')
        existing.website_url = request.form.get('website_url')
        if image_path:
            existing.image_file = image_path
    else:
        payment = AdvertPayment.query.filter_by(user_id=current_user.id).first()
        advert = Advertisement(
            user_id=current_user.id,
            business_name=request.form.get('business_name'),
            description=request.form.get('description'),
            contact_info=request.form.get('contact_info'),
            website_url=request.form.get('website_url'),
            image_file=image_path,
            package=payment.package if payment else '3months'
        )
        db.session.add(advert)

    db.session.commit()
    notify_advert_submitted(current_user)
    flash('Advert submitted! Admin will review and publish it shortly.', 'success')
    return redirect(url_for('advertiser.dashboard'))
