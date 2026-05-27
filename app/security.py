from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bleach
import os

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://"
)

ALLOWED_EXTENSIONS = {
    'proof': {'png', 'jpg', 'jpeg', 'gif', 'pdf'},
    'resume': {'pdf', 'doc', 'docx'},
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
}

def allowed_file(filename, filetype='proof'):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(filetype, set())

def sanitize(text):
    """Strip all HTML tags from user input"""
    if text:
        return bleach.clean(text, tags=[], strip=True)
    return text
