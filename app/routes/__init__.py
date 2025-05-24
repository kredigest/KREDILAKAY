# KREDILAKAY/app/routes/__init__.py
from flask import Blueprint
from flask_restx import Api
from .admin import api as admin_ns
from .client import api as client_ns
from .auditor import api as auditor_ns
from app.services.auth import jwt

# Configuration de l'API principale
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

api = Api(
    api_v1,
    version='1.0',
    title='KrediLakay API',
    description='API pour la gestion des microcrédits en Haïti',
    security='Bearer Auth',
    authorizations={
        'Bearer Auth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    }
)

# Ajout des namespaces
api.add_namespace(admin_ns)
api.add_namespace(client_ns)
api.add_namespace(auditor_ns)

# Configuration globale JWT
@api.errorhandler(jwt.InvalidTokenError)
def handle_auth_error(e):
    return {'message': str(e)}, 401

@api.errorhandler(jwt.ExpiredSignatureError)
def handle_expired_token(e):
    return {'message': 'Token expiré'}, 401

def init_app(app):
    """Initialisation des routes"""
    app.register_blueprint(api_v1)
    
    # Enregistrement des erreurs custom
    from .errors import register_error_handlers
    register_error_handlers(app)
