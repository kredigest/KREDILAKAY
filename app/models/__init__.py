from .base import db
from .client import Client
from .loan import Loan
from .user import User
from .document import Document, DocumentSignature, DocumentVersion
from .payment import Payment
from .audit import AuditLog
from .notification import Notification
from .settings import AppSettings

# Initialisation des relations
def setup_relationships():
    """Configure les relations complexes entre modèles"""
    # Relations Client
    Client.documents = db.relationship('Document', back_populates='client')
    Client.loans = db.relationship('Loan', back_populates='client')

    # Relations Document
    Document.signatures = db.relationship(
        'DocumentSignature',
        back_populates='document',
        cascade='all, delete-orphan'
    )
    Document.versions = db.relationship(
        'DocumentVersion',
        back_populates='document',
        order_by='DocumentVersion.version_number.desc()',
        cascade='all, delete-orphan'
    )

    # Relations croisées
    Payment.loan = db.relationship('Loan', back_populates='payments')
    Loan.documents = db.relationship('Document', back_populates='loan')

__all__ = [
    'Client',
    'Loan',
    'User',
    'Document',
    'DocumentSignature',
    'DocumentVersion',
    'Payment',
    'AuditLog',
    'Notification',
    'AppSettings'
]
