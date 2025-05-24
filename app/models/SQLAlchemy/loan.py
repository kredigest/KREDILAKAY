from datetime import datetime, timedelta
from decimal import Decimal
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB

class Loan(db.Model):
    __tablename__ = 'loans'
    __table_args__ = {'schema': 'kredilakay'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    client_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.clients.id'), nullable=False)
    officer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.users.id'))
    amount = db.Column(db.Numeric(12, 2), nullable=False)  # Montant principal
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)  # Taux annuel
    duration = db.Column(db.Integer, nullable=False)  # Durée en mois
    purpose = db.Column(db.String(100))  # Motif du prêt
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected/paid
    disbursement_date = db.Column(db.Date)
    repayment_frequency = db.Column(db.String(10), default='monthly')  # monthly/weekly
    metadata = db.Column(JSONB)  # {collateral: {}, guarantors: []}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    client = db.relationship('Client', back_populates='loans')
    officer = db.relationship('User', back_populates='processed_loans')
    payments = db.relationship('Payment', back_populates='loan', cascade='all, delete-orphan')
    documents = db.relationship('Document', back_populates='loan', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Loan {self.amount} HTG for Client {self.client_id}>'

    @property
    def total_interest(self):
        """Calcule l'intérêt total sur la durée du prêt"""
        monthly_rate = Decimal(self.interest_rate) / Decimal(100) / Decimal(12)
        return round(self.amount * monthly_rate * self.duration, 2)

    @property
    def total_amount(self):
        """Montant total à rembourser"""
        return round(self.amount + self.total_interest, 2)

    def generate_repayment_schedule(self):
        """Génère un échéancier de remboursement"""
        if not self.disbursement_date:
            raise ValueError("Date de décaissement non définie")

        schedule = []
        monthly_payment = self.total_amount / self.duration

        for i in range(1, self.duration + 1):
            due_date = self.disbursement_date + timedelta(days=30*i)
            schedule.append({
                'installment_number': i,
                'due_date': due_date,
                'amount': monthly_payment,
                'status': 'pending'
            })

        return schedule

    def get_current_balance(self):
        """Calcule le solde restant"""
        paid = sum(p.amount for p in self.payments if p.status == 'completed')
        return max(self.total_amount - paid, Decimal('0.00'))

    def to_dict(self):
        """Représentation JSON du prêt"""
        return {
            'id': str(self.id),
            'amount': float(self.amount),
            'interest_rate': float(self.interest_rate),
            'duration': self.duration,
            'status': self.status,
            'total_amount': float(self.total_amount),
            'balance': float(self.get_current_balance())
        }
