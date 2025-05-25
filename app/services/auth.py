from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify

class AuthError(Exception):
    """Exception personnalisée pour les erreurs d'authentification"""
    def __init__(self, message, status_code=403):
        super().__init__(message)
        self.status_code = status_code

def roles_required(*required_roles):
    """Décorateur pour vérifier les rôles dans le JWT"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_roles = claims.get('roles', [])
            if not any(role in user_roles for role in required_roles):
                raise AuthError(f"Accès refusé - Rôles requis : {required_roles}", 403)
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def admin_required(fn):
    """Décorateur pour accès strictement réservé aux administrateurs"""
    return roles_required('admin')(fn)
