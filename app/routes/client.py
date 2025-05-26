from flask_restx import Namespace, Resource
from app.services.auth import AuthService

api = Namespace('client', description='Espace sécurisé client')

@api.route('/espace')
class ClientEspace(Resource):
    @AuthService.require_roles('client', 'premium')
    def get(self):
        return {"message": "Bienvenue dans l’espace client"}, 200
