# KREDILAKAY/app/routes/webhooks.py
from flask import request, jsonify
from flask_restx import Namespace, Resource
import hmac
import hashlib
from datetime import datetime
from app.database import get_db
from app.models import Payment, AuditLog
from config import settings

api = Namespace('webhooks', description='Endpoints pour les intégrations tierces')

# Configuration des fournisseurs
PROVIDERS = {
    'NATCOM_PAY': {
        'secret': settings.NATCOM_SECRET,
        'header': 'X-Natcom-Signature'
    },
    'DIGICEL_PAY': {
        'secret': settings.DIGICEL_SECRET,
        'header': 'X-Digicel-Signature'
    },
    'UNIBANK': {
        'secret': settings.UNIBANK_SECRET,
        'header': 'X-Unibank-Signature'
    }
}

@api.route('/payment/<string:provider>')
class PaymentWebhook(Resource):
    def post(self, provider):
        """Webhook pour les notifications de paiement"""
        if provider not in PROVIDERS:
            return {'message': 'Fournisseur non supporté'}, 400

        # Vérification de la signature
        if not self._verify_signature(provider, request):
            self._log_attempt(provider, 'Signature invalide', request)
            return {'message': 'Signature invalide'}, 403

        data = request.get_json()
        payment_data = self._normalize_payment_data(provider, data)

        with get_db() as db:
            try:
                payment = Payment(
                    id=str(uuid.uuid4()),
                    loan_id=payment_data['loan_id'],
                    amount=Decimal(str(payment_data['amount'])),
                    payment_method=f"{provider}_MOBILE",
                    receipt_number=payment_data['transaction_id'],
                    payment_date=datetime.utcnow(),
                    metadata={
                        'provider': provider,
                        'raw_data': data
                    }
                )
                db.add(payment)
                
                # Mise à jour du statut du prêt si complètement payé
                self._update_loan_status(db, payment.loan_id)
                
                db.commit()
                
                self._log_attempt(provider, 'Paiement enregistré', payment_data)
                return {'message': 'Paiement enregistré'}, 200

            except Exception as e:
                db.rollback()
                self._log_attempt(provider, str(e), payment_data)
                return {'message': 'Erreur de traitement'}, 500

    def _verify_signature(self, provider, request):
        """Vérification HMAC de la signature du webhook"""
        secret = PROVIDERS[provider]['secret']
        signature_header = PROVIDERS[provider]['header']
        received_sign = request.headers.get(signature_header)
        
        if not received_sign:
            return False
            
        expected_sign = hmac.new(
            secret.encode('utf-8'),
            request.data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(received_sign, expected_sign)

    def _normalize_payment_data(self, provider, data):
        """Normalise les données de paiement selon le fournisseur"""
        # Adapté aux formats spécifiques des providers haïtiens
        if provider == 'NATCOM_PAY':
            return {
                'transaction_id': data['transactionId'],
                'amount': data['amount']['value'],
                'loan_id': data['reference'].split('_')[-1],
                'currency': data['amount']['currency']
            }
        elif provider == 'DIGICEL_PAY':
            return {
                'transaction_id': data['txn_id'],
                'amount': data['amount'],
                'loan_id': data['client_ref'],
                'currency': 'HTG'
            }
        else:  # UNIBANK
            return {
                'transaction_id': data['payment']['id'],
                'amount': data['payment']['amount'],
                'loan_id': data['payment']['reference'],
                'currency': data['payment']['currency']
            }

    def _update_loan_status(self, db, loan_id):
        """Met à jour le statut du prêt si totalement payé"""
        loan = db.query(Loan).filter_by(id=loan_id).first()
        if not loan:
            return
            
        total_paid = sum(p.amount for p in loan.payments)
        if total_paid >= loan.total_due:
            loan.status = 'PAID'
            loan.end_date = datetime.utcnow()

    def _log_attempt(self, provider, status, data):
        """Journalise les tentatives de webhook"""
        with get_db() as db:
            log = AuditLog(
                id=str(uuid.uuid4()),
                event_type='WEBHOOK',
                provider=provider,
                status=status,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                metadata={
                    'data': data,
                    'headers': dict(request.headers)
                }
            )
            db.add(log)
            db.commit()

@api.route('/disbursement/<string:provider>')
class DisbursementWebhook(Resource):
    def post(self, provider):
        """Webhook pour les confirmations de décaissement"""
        # Implémentation similaire avec validation spécifique
        pass
