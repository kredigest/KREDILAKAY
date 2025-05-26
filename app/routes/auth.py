# KREDILAKAY/app/routes/auth.py
from flask import request
from flask_restx import Namespace, Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User
from app.schemas.auth import AuthSchema
from config import settings

from flask_jwt_extended import create_access_token

def generate_token(user):
    return create_access_token(
        identity={'id': str(user.id), 'email': user.email, 'role': user.role},
        additional_claims={'roles': [user.role]}
    )
api = Namespace('auth', description='Authentification et gestion des accès')

# Modèles Swagger
login_model = api.model('Login', {
    'email': fields.String(required=True, example='client@kredilakay.ht'),
    'password': fields.String(required=True, example='securePassword123')
})

@api.route('/login')
class AuthLogin(Resource):
    @api.expect(login_model)
    @api.response(401, 'Authentification échouée')
    def post(self):
        """Connexion JWT avec vérification MFA"""
        data = request.get_json()
        schema = AuthSchema()
        errors = schema.validate(data)
        if errors:
            return {'message': 'Données invalides', 'errors': errors}, 400

        with get_db() as db:
            user = db.query(User).filter_by(email=data['email']).first()
            if not user or not check_password_hash(user.password_hash, data['password']):
                return {'message': 'Email ou mot de passe incorrect'}, 401

            # Vérification MFA si activé
            if user.mfa_enabled:
                return {
                    'message': 'Validation MFA requise',
                    'mfa_required': True,
                    'temp_token': self._generate_temp_token(user.id)
                }, 202

            access_token = self._generate_jwt_token(user)
            return {
                'access_token': access_token,
                'token_type': 'bearer'
            }, 200

    def _generate_temp_token(self, user_id):
        """Génère un token temporaire pour la validation MFA"""
        return jwt.encode(
            {
                'sub': user_id,
                'exp': datetime.utcnow() + timedelta(minutes=5),
                'type': 'mfa_temp'
            },
            settings.JWT_SECRET,
            algorithm='HS256'
        )

    def _generate_jwt_token(self, user):
        """Génère le JWT final avec les claims appropriés"""
        token_data = {
            'sub': user.id,
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=8),
            'iss': 'kredilakay-auth',
            'aud': 'kredilakay-client'
        }
        return jwt.encode(token_data, settings.JWT_SECRET, algorithm='HS256')

@api.route('/mfa/verify')
class MfaVerify(Resource):
    @api.doc(security='Bearer')
    @api.expect(api.model('MFA', {
        'code': fields.String(required=True, example='123456'),
        'temp_token': fields.String(required=True)
    }))
    def post(self):
        """Validation du code MFA"""
        data = request.get_json()
        try:
            temp_token = jwt.decode(
                data['temp_token'],
                settings.JWT_SECRET,
                algorithms=['HS256'],
                audience='kredilakay-client'
            )
        except jwt.PyJWTError:
            return {'message': 'Token temporaire invalide'}, 401

        # Ici, intégrer votre logique de vérification TOTP
        # Exemple avec PyOTP: totp.verify(data['code'])
        is_valid = True  # Remplacer par la vraie vérification

        if not is_valid:
            return {'message': 'Code MFA invalide'}, 401

        with get_db() as db:
            user = db.query(User).get(temp_token['sub'])
            if not user:
                return {'message': 'Utilisateur introuvable'}, 404

            access_token = self._generate_jwt_token(user)
            return {
                'access_token': access_token,
                'token_type': 'bearer'
            }, 200

@api.route('/refresh')
class TokenRefresh(Resource):
    @api.doc(security='Bearer')
    def post(self):
        """Rafraîchissement du token JWT"""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {'message': 'Token manquant'}, 401

        try:
            token = auth_header.split()[1]
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=['HS256'],
                options={'verify_exp': False}
            )
            
            # Vérifier que le token est expiré mais valide
            if datetime.utcnow() < datetime.fromtimestamp(payload['exp']):
                return {'message': 'Token pas encore expiré'}, 400

            # Générer un nouveau token
            new_token = jwt.encode(
                {
                    'sub': payload['sub'],
                    'email': payload['email'],
                    'role': payload['role'],
                    'exp': datetime.utcnow() + timedelta(hours=8)
                },
                settings.JWT_SECRET,
                algorithm='HS256'
            )
            return {
                'access_token': new_token,
                'token_type': 'bearer'
            }, 200

        except jwt.PyJWTError:
            return {'message': 'Token invalide'}, 401
