from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_talisman import Talisman
from app.security import limiter
import os

mail = Mail()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    try:
        from dotenv import load_dotenv
        load_dotenv('/etc/jobboard.env')
        load_dotenv()
    except ImportError:
        pass

    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        from config import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)

    # Init extensions
    from app.models import db, User
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    # Rate limiter
    limiter.init_app(app)

    # Security headers (Talisman)
    csp = {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
            'fonts.googleapis.com',
        ],
        'font-src': [
            "'self'",
            'fonts.googleapis.com',
            'fonts.gstatic.com',
            'cdnjs.cloudflare.com',
        ],
        'img-src': ["'self'", 'data:', '*'],
    }

    if env == 'production':
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            content_security_policy=csp,
            referrer_policy='strict-origin-when-cross-origin',
            feature_policy={
                'geolocation': "'none'",
                'camera': "'none'",
                'microphone': "'none'",
            }
        )

    # Africa's Talking
    from app.notifications import init_africastalking
    with app.app_context():
        init_africastalking(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth
    from app.routes.employer import employer
    from app.routes.jobseeker import jobseeker
    from app.routes.admin import admin_bp
    from app.routes.public import public
    from app.routes.advertiser import advertiser

    app.register_blueprint(auth)
    app.register_blueprint(employer)
    app.register_blueprint(jobseeker)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public)
    app.register_blueprint(advertiser)

    # Create tables
    with app.app_context():
        db.create_all()
        create_default_admin(app)

    return app


def create_default_admin(app):
    with app.app_context():
        from app.models import User, db
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                name='Administrator',
                email='admin@jobboard.co.zw',
                phone='+263772555263',
                password=generate_password_hash('Letsconnect#2026'),
                role='admin',
                is_approved=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created: admin@jobboard.co.zw / admin1234")
