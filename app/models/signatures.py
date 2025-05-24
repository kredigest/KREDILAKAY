
from datetime import datetime
from enum import Enum
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import event, CheckConstraint

class SignatureType(Enum):
    ELECTRONIC = 'electronic'
    BIOMETRIC = 'biometric'
    DIGITAL = 'digital'  # Certificat numérique
    MANUAL = 'manual'   # Scan de signature manuscrite

class SignatureStatus(Enum):
    DRAFT = 'draft'
    PENDING = 'pending'
    SIGNED = 'signed'
    EXPIRED = 'expired'
    REVOKED = 'revoked'

class DocumentSignature(db.Model):
    __tablename__ = 'document_signatures'
    __table_args__ = (
        {'schema': 'kredilakay'},
        CheckConstraint('signer_id IS NOT NULL OR external_signer IS NOT NULL', 
                      name='signer_required')
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.documents.id'), nullable=False)
    signer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.users.id'))  # Null pour signataires externes
    external_signer = db.Column(JSONB)  # {name: "", email: "", phone: ""}
    signature_type = db.Column(db.Enum(SignatureType), nullable=False)
    status = db.Column(db.Enum(SignatureStatus), default=SignatureStatus.PENDING)
    signature_data = db.Column(db.Text)  # Base64 ou JSON selon le type
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    signed_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    metadata = db.Column(JSONB)  # {certificate: {}, device: {}}
    audit_log = db.Column(JSONB)  # Historique des actions

    # Relations
    document = db.relationship('Document', back_populates='signatures')
    signer = db.relationship('User', back_populates='signatures')

    def __repr__(self):
        return f'<Signature {self.signature_type.value} on doc {self.document_id}>'

    def sign(self, signature_data):
        """Enregistre une signature"""
        self.signature_data = signature_data
        self.status = SignatureStatus.SIGNED
        self.signed_at = datetime.utcnow()
        self._log_action('signed')
        return self

    def revoke(self, reason):
        """Révoque une signature"""
        self.status = SignatureStatus.REVOKED
        self._log_action('revoked', {'reason': reason})
        return self

    def _log_action(self, action, extra=None):
        """Journalise les actions sur la signature"""
        if not self.audit_log:
            self.audit_log = []
        
        log_entry = {
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'by': str(self.signer_id) if self.signer_id else 'external'
        }
        if extra:
            log_entry.update(extra)
        
        self.audit_log.append(log_entry)

class SignatureRequest(db.Model):
    __tablename__ = 'signature_requests'
    __table_args__ = {'schema': 'kredilakay'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    initiator_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.users.id'), nullable=False)
    document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.documents.id'), nullable=False)
    signature_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.document_signatures.id'))
    token = db.Column(db.String(64), unique=True, nullable=False)  # JETON D'ACCÈS
    expires_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    metadata = db.Column(JSONB)  # {message: "", reminders: []}

    # Relations
    initiator = db.relationship('User', foreign_keys=[initiator_id])
    document = db.relationship('Document')
    signature = db.relationship('DocumentSignature')

    def is_valid(self):
        return self.expires_at > datetime.utcnow() and not self.completed_at

# Event listeners
@event.listens_for(DocumentSignature, 'before_insert')
def set_default_expiration(mapper, connection, target):
    if target.expires_at is None and target.status == SignatureStatus.PENDING:
        target.expires_at = datetime.utcnow() + timedelta(days=7)
