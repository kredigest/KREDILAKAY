# KREDILAKAY/app/routes/documents.py
from flask import request, send_file
from flask_restx import Namespace, Resource, fields
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from app.services.pdf.generator import PDFContractGenerator
from app.services.pdf.signature import DigitalSigner
from app.pdf_services.storage import PDFStorage
from app.database import get_db
from app.models import Document, Loan
from config import settings
from .auth import roles_required

api = Namespace('documents', description='Gestion des documents contractuels')

# Modèles Swagger
document_model = api.model('Document', {
    'loan_id': fields.String(required=True, description='ID du prêt associé'),
    'document_type': fields.String(required=True, enum=['CONTRACT', 'IDENTITY', 'PROOF'])
})

signature_model = api.model('Signature', {
    'signature_data': fields.String(required=True, description='Signature en base64'),
    'signature_position': fields.List(fields.Integer, description='[x, y, page]')
})

@api.route('/generate-contract/<string:loan_id>')
class ContractGeneration(Resource):
    @roles_required('admin', 'client')
    def get(self, loan_id):
        """Génère un contrat PDF pour un prêt spécifique"""
        with get_db() as db:
            loan = db.query(Loan).filter_by(id=loan_id).first()
            if not loan:
                return {'message': 'Prêt non trouvé'}, 404
            
            # Génération du PDF
            pdf_generator = PDFContractGenerator(loan)
            pdf_data = pdf_generator.generate()
            
            return {
                'pdf_data': pdf_data.decode('latin1'),
                'loan_id': loan_id
            }, 200

@api.route('/upload-signature')
class SignatureUpload(Resource):
    @api.expect(signature_model)
    @roles_required('client')
    def post(self):
        """Enregistre une signature numérique pour un document"""
        data = request.get_json()
        
        # Validation de la signature
        if not DigitalSigner.validate_signature(data['signature_data']):
            return {'message': 'Signature invalide'}, 400
            
        with get_db() as db:
            # Stockage en base de données
            signature = Document(
                id=str(uuid.uuid4()),
                document_type='SIGNATURE',
                content=data['signature_data'],
                loan_id=data.get('loan_id'),
                created_at=datetime.utcnow()
            )
            db.add(signature)
            db.commit()
            
            return {
                'signature_id': signature.id,
                'message': 'Signature enregistrée avec succès'
            }, 201

@api.route('/sign-contract/<string:document_id>')
class ContractSigning(Resource):
    @api.expect(signature_model)
    @roles_required('client')
    def post(self, document_id):
        """Appose une signature numérique sur un contrat existant"""
        data = request.get_json()
        
        with get_db() as db:
            document = db.query(Document).filter_by(id=document_id).first()
            if not document:
                return {'message': 'Document non trouvé'}, 404
                
            # Signer le document
            signer = DigitalSigner(document.content)
            signed_pdf = signer.apply_signature(
                data['signature_data'],
                position=data['signature_position']
            )
            
            # Stockage sécurisé
            storage = PDFStorage()
            meta = storage.save_contract(signed_pdf, document.loan_id)
            
            # Mise à jour du document
            document.is_signed = True
            document.signed_version = meta['filepath']
            document.signed_at = datetime.utcnow()
            db.commit()
            
            return {
                'document_id': document.id,
                'storage_path': meta['filepath'],
                'checksum': meta['checksum']
            }, 200

@api.route('/download/<string:document_id>')
class DocumentDownload(Resource):
    @roles_required('admin', 'client', 'auditor')
    def get(self, document_id):
        """Télécharge un document signé"""
        with get_db() as db:
            document = db.query(Document).filter_by(id=document_id).first()
            if not document or not document.is_signed:
                return {'message': 'Document signé non disponible'}, 404
                
            storage = PDFStorage()
            try:
                pdf_data = storage.retrieve_contract(document.signed_version)
                return send_file(
                    pdf_data,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"contrat_{document.loan_id}.pdf"
                )
            except Exception as e:
                return {'message': str(e)}, 500

@api.route('/verify/<string:document_id>')
class DocumentVerification(Resource):
    @roles_required('admin', 'auditor')
    def get(self, document_id):
        """Vérifie l'intégrité et la validité d'un document"""
        with get_db() as db:
            document = db.query(Document).filter_by(id=document_id).first()
            if not document:
                return {'message': 'Document non trouvé'}, 404
                
            # Vérification cryptographique
            verifier = DigitalSigner(document.content)
            verification = verifier.verify_document()
            
            return {
                'document_id': document.id,
                'is_valid': verification['valid'],
                'signature_details': verification['signatures'],
                'checksum_match': verification['checksum_valid']
            }, 200
