# KREDILAKAY/app/routes/loans.py
from flask import request
from flask_restx import Namespace, Resource, fields
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from app.database import get_db
from app.models import Loan, Client, Payment
from app.schemas.loans import LoanSchema, PaymentSchema
from config import settings
from .auth import roles_required
from app.services.penalty import PenaltyCalculator

api = Namespace('loans', description='Gestion des prêts et échéances')

# Modèles Swagger
loan_model = api.model('Loan', {
    'client_id': fields.String(required=True),
    'amount': fields.Float(required=True),
    'duration_days': fields.Integer(required=True),
    'purpose': fields.String(required=True, enum=['EDUCATION', 'BUSINESS', 'EMERGENCY', 'OTHER'])
})

payment_model = api.model('Payment', {
    'amount': fields.Float(required=True),
    'payment_method': fields.String(required=True, enum=['CASH', 'MOBILE_MONEY', 'BANK_TRANSFER']),
    'receipt_number': fields.String()
})

@api.route('/request')
class LoanRequest(Resource):
    @api.expect(loan_model)
    @roles_required('client')
    def post(self):
        """Soumettre une nouvelle demande de prêt"""
        data = request.get_json()
        schema = LoanSchema()
        errors = schema.validate(data)
        if errors:
            return {'message': 'Données invalides', 'errors': errors}, 400

        with get_db() as db:
            client = db.query(Client).filter_by(id=data['client_id']).first()
            if not client:
                return {'message': 'Client non trouvé'}, 404

            # Calcul automatique des intérêts basé sur le score client
            interest_rate = self._calculate_interest_rate(client.credit_score)
            
            new_loan = Loan(
                id=str(uuid.uuid4()),
                client_id=client.id,
                amount=Decimal(str(data['amount'])),
                interest_rate=Decimal(str(interest_rate)),
                duration_days=data['duration_days'],
                purpose=data['purpose'],
                status='PENDING',
                request_date=datetime.utcnow()
            )
            
            db.add(new_loan)
            db.commit()
            
            return {
                'loan_id': new_loan.id,
                'amount': float(new_loan.amount),
                'interest_rate': float(interest_rate),
                'total_due': float(new_loan.total_due),
                'status': new_loan.status
            }, 201

    def _calculate_interest_rate(self, credit_score):
        """Calcule le taux d'intérêt basé sur le score de crédit"""
        base_rate = Decimal('0.15')  # 15% de base
        risk_adjustment = (Decimal('1') - credit_score) * Decimal('0.1')
        return max(base_rate + risk_adjustment, Decimal('0.05'))  # Minimum 5%

@api.route('/<string:loan_id>')
class LoanDetail(Resource):
    @roles_required('admin', 'client', 'auditor')
    def get(self, loan_id):
        """Obtenir les détails d'un prêt spécifique"""
        with get_db() as db:
            loan = db.query(Loan).filter_by(id=loan_id).first()
            if not loan:
                return {'message': 'Prêt non trouvé'}, 404
            
            payment_schedule = self._generate_payment_schedule(loan)
            
            return {
                'loan': self._serialize_loan(loan),
                'payment_schedule': payment_schedule,
                'penalties': self._calculate_penalties(loan)
            }, 200

    def _generate_payment_schedule(self, loan):
        """Génère le calendrier de remboursement"""
        schedule = []
        daily_payment = loan.total_due / loan.duration_days
        current_date = loan.start_date if loan.start_date else datetime.utcnow().date()
        
        for day in range(1, loan.duration_days + 1):
            due_date = current_date + timedelta(days=day)
            schedule.append({
                'day': day,
                'due_date': due_date.isoformat(),
                'amount_due': float(daily_payment)
            })
        
        return schedule

    def _calculate_penalties(self, loan):
        """Calcule les pénalités en cas de retard"""
        if loan.status != 'APPROVED':
            return {'daily_penalty_rate': 0, 'total_penalty': 0}
            
        calculator = PenaltyCalculator(loan)
        return {
            'daily_penalty_rate': float(calculator.daily_rate),  # 2% par jour
            'total_penalty': float(calculator.calculate_total()),
            'days_late': calculator.days_late
        }

    def _serialize_loan(self, loan):
        return {
            'id': loan.id,
            'amount': float(loan.amount),
            'interest_rate': float(loan.interest_rate),
            'total_due': float(loan.total_due),
            'status': loan.status,
            'purpose': loan.purpose,
            'request_date': loan.request_date.isoformat()
        }

@api.route('/<string:loan_id>/payments')
class LoanPayments(Resource):
    @api.expect(payment_model)
    @roles_required('client', 'admin')
    def post(self, loan_id):
        """Enregistrer un paiement pour un prêt"""
        data = request.get_json()
        schema = PaymentSchema()
        errors = schema.validate(data)
        if errors:
            return {'message': 'Données invalides', 'errors': errors}, 400

        with get_db() as db:
            loan = db.query(Loan).filter_by(id=loan_id).first()
            if not loan:
                return {'message': 'Prêt non trouvé'}, 404
                
            if loan.status != 'APPROVED':
                return {'message': 'Prêt non approuvé'}, 400
                
            payment = Payment(
                id=str(uuid.uuid4()),
                loan_id=loan.id,
                amount=Decimal(str(data['amount'])),
                payment_method=data['payment_method'],
                receipt_number=data.get('receipt_number'),
                payment_date=datetime.utcnow()
            )
            
            db.add(payment)
            loan.last_payment_date = payment.payment_date
            db.commit()
            
            return {
                'payment_id': payment.id,
                'amount': float(payment.amount),
                'remaining_balance': float(self._calculate_remaining_balance(loan))
            }, 201

    def _calculate_remaining_balance(self, loan):
        """Calcule le solde restant après paiement"""
        total_paid = sum(p.amount for p in loan.payments)
        return max(loan.total_due - total_paid, Decimal('0'))

@api.route('/<string:loan_id>/status')
class LoanStatus(Resource):
    @roles_required('admin')
    def patch(self, loan_id):
        """Mettre à jour le statut d'un prêt (Admin only)"""
        data = request.get_json()
        
        valid_statuses = ['APPROVED', 'REJECTED', 'PAID', 'DEFAULTED']
        if data.get('status') not in valid_statuses:
            return {'message': 'Statut invalide'}, 400
            
        with get_db() as db:
            loan = db.query(Loan).filter_by(id=loan_id).first()
            if not loan:
                return {'message': 'Prêt non trouvé'}, 404
                
            loan.status = data['status']
            if data['status'] == 'APPROVED':
                loan.start_date = datetime.utcnow().date()
            elif data['status'] == 'PAID':
                loan.end_date = datetime.utcnow()
                
            db.commit()
            
            return {
                'loan_id': loan.id,
                'new_status': loan.status,
                'updated_at': datetime.utcnow().isoformat()
            }, 200
