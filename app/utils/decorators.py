from functools import wraps
from flask import abort, make_response
from flask_login import current_user

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Polymorphic check: Does the user have the required role?
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized: User is not logged in
            if current_user.role != role.lower():
                abort(403)  # Forbidden: User is logged in but has the wrong role
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def no_cache(f):
    """Prevents caching for a given route during development."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return decorated_function