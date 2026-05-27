import africastalking
from flask_mail import Message
from flask import current_app


def init_africastalking(app):
    africastalking.initialize(
        username=app.config['AT_USERNAME'],
        api_key=app.config['AT_API_KEY']
    )


def notify_admin(subject, email_body, sms_body=None):
    """Send Email + SMS to admin instantly"""
    _send_email(subject, email_body)
    _send_sms(sms_body if sms_body else email_body[:160])


def _send_email(subject, body):
    from app import mail
    try:
        msg = Message(
            subject=f"[JobBoard] {subject}",
            recipients=[current_app.config['ADMIN_EMAIL']],
            body=body
        )
        mail.send(msg)
    except Exception as e:
        print(f"[Email Error] {e}")


def _send_sms(body):
    try:
        sms = africastalking.SMS
        sms.send(body[:160], [current_app.config['ADMIN_PHONE']])
    except Exception as e:
        print(f"[SMS Error] {e}")


# ─── Notification Events ────────────────────────────────────────────

def notify_new_employer(user):
    notify_admin(
        subject="New Employer Registered!",
        email_body=(
            f"A new employer has registered and is awaiting your review.\n\n"
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone}\n"
            f"Registered At: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Login to the admin dashboard to review."
        ),
        sms_body=f"[JobBoard] New Employer: {user.name} ({user.email}) just registered. Check dashboard."
    )


def notify_new_jobseeker(user):
    notify_admin(
        subject="New Job Seeker Registered!",
        email_body=(
            f"A new job seeker has registered and is awaiting your review.\n\n"
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone}\n"
            f"Registered At: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Login to the admin dashboard to review."
        ),
        sms_body=f"[JobBoard] New Job Seeker: {user.name} ({user.email}) just registered. Check dashboard."
    )


def notify_payment_proof(user):
    notify_admin(
        subject="Payment Proof Uploaded!",
        email_body=(
            f"A user has uploaded payment proof and is awaiting confirmation.\n\n"
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone}\n"
            f"Role: {user.role.capitalize()}\n\n"
            f"Login to the admin dashboard to confirm or reject the payment."
        ),
        sms_body=f"[JobBoard] Payment proof from {user.name} ({user.role}). Login to confirm."
    )


def notify_job_request(user, job_request):
    notify_admin(
        subject="New Job Request Submitted!",
        email_body=(
            f"An employer has submitted a job request for you to post.\n\n"
            f"Employer: {user.name}\n"
            f"Company: {job_request.company_name}\n"
            f"Job Title: {job_request.job_title}\n"
            f"Location: {job_request.location}\n\n"
            f"Login to the admin dashboard to create the listing."
        ),
        sms_body=f"[JobBoard] New job request from {user.name}: {job_request.job_title}. Check dashboard."
    )


def notify_profile_submitted(user):
    notify_admin(
        subject="Job Seeker Profile Submitted!",
        email_body=(
            f"A job seeker has submitted their profile for you to publish.\n\n"
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone}\n\n"
            f"Login to the admin dashboard to review and publish."
        ),
        sms_body=f"[JobBoard] Profile submitted by {user.name}. Login to publish."
    )


def notify_new_inquiry(inquiry, reference_title):
    notify_admin(
        subject="New Inquiry from Visitor!",
        email_body=(
            f"Someone is interested and needs your assistance.\n\n"
            f"Visitor Name: {inquiry.visitor_name}\n"
            f"Visitor Email: {inquiry.visitor_email}\n"
            f"Visitor Phone: {inquiry.visitor_phone}\n"
            f"Interested In: {reference_title}\n"
            f"Type: {inquiry.inquiry_type.capitalize()}\n"
            f"Message: {inquiry.message}\n\n"
            f"Please contact them as soon as possible."
        ),
        sms_body=f"[JobBoard] New inquiry from {inquiry.visitor_name} ({inquiry.visitor_phone}) about {reference_title}. Contact them now!"
    )


def notify_user_activation(user):
    """Email the user when admin approves their account"""
    from app import mail
    try:
        msg = Message(
            subject="[JobBoard] Your Account Has Been Activated!",
            recipients=[user.email],
            body=(
                f"Dear {user.name},\n\n"
                f"Great news! Your payment has been confirmed and your account is now active.\n\n"
                f"You can now log in to your dashboard.\n\n"
                f"Thank you for choosing our platform.\n\n"
                f"Best regards,\nJobBoard Admin"
            )
        )
        mail.send(msg)
    except Exception as e:
        print(f"[Activation Email Error] {e}")


def notify_new_advertiser(user):
    notify_admin(
        subject="New Advertiser Registered!",
        email_body=(
            f"A new advertiser has registered.\n\n"
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone}\n\n"
            f"Login to the admin dashboard to review."
        ),
        sms_body=f"[JobConnect] New Advertiser: {user.name} registered. Check dashboard."
    )


def notify_advert_payment(user, package):
    from app.models import AD_PACKAGES
    pkg = AD_PACKAGES.get(package, {})
    notify_admin(
        subject="Advertiser Payment Proof Uploaded!",
        email_body=(
            f"An advertiser has uploaded payment proof.\n\n"
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone}\n"
            f"Package: {pkg.get('label','?')} — ${pkg.get('price','?')}\n\n"
            f"Login to confirm the payment."
        ),
        sms_body=f"[JobConnect] Advert payment from {user.name} - {pkg.get('label','?')} package. Confirm now!"
    )


def notify_advert_submitted(user):
    notify_admin(
        subject="New Advert Submitted!",
        email_body=(
            f"An advertiser has submitted their advert for publishing.\n\n"
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone}\n\n"
            f"Login to review and publish the advert."
        ),
        sms_body=f"[JobConnect] Advert submitted by {user.name}. Login to publish."
    )
