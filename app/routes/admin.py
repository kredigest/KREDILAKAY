from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

api = Namespace('admin', description='Opérations administratives pour KrediLakay')

# === Modèles Swagger ===

admin_model = api.model('Admin', {
    'id': fields.String(readonly=True, description='Identifiant admin'),
    'email': fields.String(required=True, description='Adresse email'),
    'role': fields.String(description='Rôle administratif (ex: superadmin, agent)')
})

admin_response = api.model('AdminResponse', {
    'status': fields.String(required=True, example='OK'),
    'message': fields.String(example='Accès autorisé'),
    'user': fields.String(description='Identifiant de l’utilisateur connecté'),
})

# === Données fictives pour test local ===
ADMIN_LIST = [
    {'id': '1', 'email': 'admin@kredilakay.ht', 'role': 'superadmin'},
    {'id': '2', 'email': 'validator@kredilakay.ht', 'role': 'agent'},
]

# === Endpoints ===

@api.route('/healthcheck')
class AdminHealth(Resource):
    @api.doc(security='Bearer Auth')
    @api.marshal_with(admin_response)
    @jwt_required()
    def get(self):
        """Vérification d’accès admin (JWT requis)"""
        current_user = get_jwt_identity()

        if not current_user or current_user.get('role') != 'admin':
            api.abort(403, "Accès refusé : privilèges administrateur requis.")

        return {
            'status': 'OK',
            'message': 'Accès autorisé',
            'user': current_user.get('email', 'non identifié')
        }, 200


@api.route('/all')
class AdminList(Resource):
    @api.doc(security='Bearer Auth')
    @api.marshal_list_with(admin_model)
    @jwt_required()
    def get(self):
        """Liste de tous les administrateurs (protégé)"""
        current_user = get_jwt_identity()
        if current_user.get('role') != 'admin':
            api.abort(403, "Accès refusé : autorisation admin requise.")
        return ADMIN_LIST


@api.route('/<string:id>')
@api.param('id', 'Identifiant de l’admin')
class AdminById(Resource):
    @api.doc(security='Bearer Auth')
    @api.marshal_with(admin_model)
    @jwt_required()
    def get(self, id):
        """Détails d’un administrateur par ID (protégé)"""
        current_user = get_jwt_identity()
        if current_user.get('role') != 'admin':
            api.abort(403, "Accès refusé : autorisation admin requise.")
        admin = next((a for a in ADMIN_LIST if a['id'] == id), None)
        if not admin:
            api.abort(404, f"Admin avec l'ID {id} introuvable")
        return admin
