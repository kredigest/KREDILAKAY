from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, create_access_token

class AuthService:
    """Service centralisé pour la gestion d'authentification et de rôles"""

    @staticmethod
    def require_roles(*required_roles):
        """Décorateur pour vérifier les rôles autorisés"""
        def wrapper(fn):
            @wraps(fn)
            def decorator(*args, **kwargs):
                verify_jwt_in_request()
                claims = get_jwt()
                user_roles = claims.get('roles', [])

                if not any(role in user_roles for role in required_roles):
                    return jsonify({
                        "error": f"Accès refusé. Rôle requis : {required_roles}"
                    }), 403

                return fn(*args, **kwargs)
            return decorator
        return wrapper

    @staticmethod
    def admin_only(fn):
        """Décorateur spécifique pour restreindre l'accès aux administrateurs"""
        return AuthService.require_roles('admin')(fn)

    @staticmethod
    def generate_token(user):
        """Génère un JWT avec rôle et email"""
        return create_access_token(
            identity={'id': str(user.id), 'email': user.email, 'role': user.role},
            additional_claims={'roles': [user.role]}
        )
