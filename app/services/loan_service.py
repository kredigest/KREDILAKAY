# KREDILAKAY/app/services/loan_service.py
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.database import get_db
from app.models import Loan, Payment, Client
from config import settings
import logging

class LoanService:
    """Service central pour la gestion des prêts et calculs financiers"""

    def __init__(self):
        self.penalty_rate = Decimal(settings.PENALTY_RATE)  # 2% par défaut
        self.grace_period = settings.GRACE_PERIOD_DAYS  # 5 jours par défaut

    def calculate_loan_terms(
        self,
        amount: Decimal,
        duration_days: int,
        client_risk_score: Decimal
    ) -> Dict:
        """
        Calcule les termes d'un prêt avant création
        Args:
            amount: Montant demandé
            duration_days: Durée en jours
            client_risk_score: Score de risque client (0-1)
        Returns:
            Dict: Termes calculés (intérêts, échéances)
        """
        interest_rate = self._determine_interest_rate(client_risk_score)
        total_interest = (amount * interest_rate * duration_days) / Decimal('365')
        total_due = amount + total_interest

        return {
            'amount': amount.quantize(Decimal('.01'),
            'interest_rate': interest_rate.quantize(Decimal('.0001')),
            'total_interest': total_interest.quantize(Decimal('.01')),
            'total_due': total_due.quantize(Decimal('.01')),
            'daily_payment': (total_due / duration_days).quantize(Decimal('.01'))
        }

    def _determine_interest_rate(self, risk_score: Decimal) -> Decimal:
        """Calcule le taux d'intérêt basé sur le risque"""
        base_rate = Decimal(settings.BASE_INTEREST_RATE)  # 15% par défaut
        risk_adjustment = (Decimal('1') - risk_score) * Decimal('0.1')  # 0-10% ajustement
        return max(
            min(base_rate + risk_adjustment, Decimal('0.3')),  # Plafond à 30%
            Decimal('0.05')  # Plancher à 5%
        )

    def generate_payment_schedule(self, loan: Loan) -> List[Dict]:
        """Génère le calendrier de paiement pour un prêt"""
        if not loan.start_date:
            raise ValueError("Date de début non définie")

        schedule = []
        daily_amount = loan.total_due / Decimal(loan.duration_days)
        remaining_balance = loan.total_due

        for day in range(1, loan.duration_days + 1):
            due_date = loan.start_date + timedelta(days=day)
            remaining_balance -= daily_amount
            schedule.append({
                'day_number': day,
                'due_date': due_date.strftime('%Y-%m-%d'),
                'amount_due': daily_amount.quantize(Decimal('.01')),
                'remaining_balance': max(remaining_balance, Decimal('0')).quantize(Decimal('.01'))
            })

        return schedule

    def record_payment(
        self,
        loan_id: str,
        amount: Decimal,
        payment_method: str,
        receipt_number: Optional[str] = None
    ) -> Dict:
        """Enregistre un paiement et met à jour le prêt"""
        with get_db() as db:
            loan = db.query(Loan).filter_by(id=loan_id).first()
            if not loan:
                raise ValueError("Prêt non trouvé")

            payment = Payment(
                id=str(uuid.uuid4()),
                loan_id=loan.id,
                amount=amount,
                payment_method=payment_method,
                receipt_number=receipt_number,
                payment_date=datetime.utcnow()
            )

            db.add(payment)
            loan.last_payment_date = payment.payment_date

            # Vérifier si le prêt est complètement remboursé
            if self._calculate_remaining_balance(loan) <= Decimal('0'):
                loan.status = 'PAID'
                loan.end_date = datetime.utcnow()

            db.commit()

            return {
                'payment_id': payment.id,
                'remaining_balance': self._calculate_remaining_balance(loan),
                'loan_status': loan.status
            }

    def _calculate_remaining_balance(self, loan: Loan) -> Decimal:
        """Calcule le solde restant d'un prêt"""
        total_paid = sum(p.amount for p in loan.payments)
        return max(loan.total_due - total_paid, Decimal('0'))

    def calculate_penalties(self, loan: Loan, as_of_date: datetime = None) -> Dict:
        """Calcule les pénalités de retard pour un prêt"""
        if loan.status != 'APPROVED' or not loan.start_date:
            return {
                'days_late': 0,
                'penalty_rate': float(self.penalty_rate),
                'penalty_amount': Decimal('0'),
                'total_due_with_penalty': loan.total_due
            }

        as_of_date = as_of_date or datetime.utcnow()
        due_date = loan.start_date + timedelta(days=loan.duration_days)
        
        if as_of_date <= due_date + timedelta(days=self.grace_period):
            return {
                'days_late': 0,
                'penalty_rate': float(self.penalty_rate),
                'penalty_amount': Decimal('0'),
                'total_due_with_penalty': loan.total_due
            }

        days_late = (as_of_date - due_date).days - self.grace_period
        penalty_amount = (loan.total_due * self.penalty_rate * days_late).quantize(Decimal('.01'))

        return {
            'days_late': days_late,
            'penalty_rate': float(self.penalty_rate),
            'penalty_amount': penalty_amount,
            'total_due_with_penalty': (loan.total_due + penalty_amount).quantize(Decimal('.01'))
        }

    def client_loan_history(self, client_id: str) -> Dict:
        """Récupère l'historique complet des prêts d'un client"""
        with get_db() as db:
            client = db.query(Client).filter_by(id=client_id).first()
            if not client:
                raise ValueError("Client non trouvé")

            loans = []
            for loan in client.loans:
                loans.append({
                    'id': loan.id,
                    'amount': float(loan.amount),
                    'status': loan.status,
                    'start_date': loan.start_date.strftime('%Y-%m-%d') if loan.start_date else None,
                    'total_paid': float(sum(p.amount for p in loan.payments)),
                    'remaining_balance': float(self._calculate_remaining_balance(loan))
                })

            return {
                'client_id': client.id,
                'credit_score': float(client.credit_score),
                'active_loans': len([l for l in loans if l['status'] == 'APPROVED']),
                'loan_history': loans
            }
