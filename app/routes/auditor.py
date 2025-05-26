# app/routes/auditor.py
from flask_restx import Namespace, Resource
from app.services.auth import roles_required
from flask_jwt_extended import jwt_required

api = Namespace('auditor', description='Espace auditeur')

@api.route('/logs')
class AuditLogs(Resource):
    @jwt_required()
    @roles_required('auditor', 'admin')
    def get(self):
        return {'logs': ['Accès', 'Modifications', 'Exportations']}
