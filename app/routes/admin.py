from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth import admin_required

api = Namespace('admin', description='Opérations administratives pour KrediLakay')

# Modèle pour Swagger
admin_model = api.model('Admin', {
    'id': fields.String(readonly=True, description='Identifiant admin'),
    'email': fields.String(required=True, description='Email'),
    'role': fields.String(description='Rôle admin'),
})

admin_response = api.model('AdminResponse', {
    'status': fields.String(required=True, example='OK'),
    'message': fields.String(example='Accès autorisé'),
    'user': fields.String(description='Utilisateur connecté'),
})

# Données fictives pour test
ADMIN_LIST = [
    {'id': '1', 'email': 'admin@kredilakay.ht', 'role': 'superadmin'},
    {'id': '2', 'email': 'validator@kredilakay.ht', 'role': 'agent'},
]

@api.route('/all')
class AdminList(Resource):
    @jwt_required()
    @admin_required
    @api.marshal_list_with(admin_model)
    def get(self):
        """Liste de tous les administrateurs"""
        return ADMIN_LIST

@api.route('/<string:id>')
@api.param('id', 'Identifiant de l’administrateur')
class AdminById(Resource):
    @jwt_required()
    @admin_required
    @api.marshal_with(admin_model)
    def get(self, id):
        """Obtenir un administrateur par ID"""
        admin = next((a for a in ADMIN_LIST if a['id'] == id), None)
        if not admin:
            api.abort(404, f"Administrateur {id} introuvable")
        return admin

@api.route('/healthcheck')
class AdminHealth(Resource):
    @jwt_required()
    @admin_required
    @api.marshal_with(admin_response)
    def get(self):
        """Vérifie l'accès admin via JWT"""
        current_user = get_jwt_identity()
        return {
            'status': 'OK',
            'message': 'Accès autorisé',
            'user': current_user.get('email', 'inconnu')
        }
