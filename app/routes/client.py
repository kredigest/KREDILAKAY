from flask_restx import Namespace, Resource
from app.services.auth import roles_required

api = Namespace('client', description='Opérations clients')

@api.route('/loans')
class ClientLoans(Resource):
    @roles_required('client')
    def get(self):
        """Liste des prêts du client"""
        return {"loans": []}, 200
