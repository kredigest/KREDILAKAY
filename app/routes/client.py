# app/routes/client.py
from flask_restx import Namespace, Resource
from app.services.auth import roles_required
from flask_jwt_extended import jwt_required

api = Namespace('client', description='Espace client sécurisé')

@api.route('/dashboard')
class ClientDashboard(Resource):
    @jwt_required()
    @roles_required('client', 'premium_client')
    def get(self):
        return {'message': 'Bienvenue, client !'}
