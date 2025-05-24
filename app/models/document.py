from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSONB, UUID

class Document(db.Model):
__tablename__ = 'documents'
__table_args__ = {'schema': 'kredilakay'}

id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
client_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.clients.id'), nullable=False)
loan_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.loans.id'))
document_type = db.Column(db.String(50), nullable=False) # contract, receipt, identity
file_path = db.Column(db.String(255), nullable=False)
file_hash = db.Column(db.String(64), nullable=False) # SHA-256
storage_type = db.Column(db.String(20), default='s3') # s3, local, encrypted
metadata = db.Column(JSONB) # {pages: 5, format: 'A4', watermark: true}
status = db.Column(db.String(20), default='pending') # pending, signed, expired
created_at = db.Column(db.DateTime, default=datetime.utcnow)
updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Relations
client = db.relationship('Client', backref='documents')
loan = db.relationship('Loan', backref='documents')
signatures = db.relationship('DocumentSignature', backref='document', cascade='all, delete-orphan')
versions = db.relationship('DocumentVersion', backref='document', cascade='all, delete-orphan')

def __repr__(self):
return f'<Document {self.document_type} for Client {self.client_id}>'

def get_signed_url(self, expires_in=3600):
from app.services.storage import get_presigned_url
return get_presigned_url(self.file_path, expires_in)

class DocumentSignature(db.Model):
__tablename__ = 'document_signatures'
__table_args__ = {'schema': 'kredilakay'}

id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.documents.id'), nullable=False)
user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.users.id'))
signature_type = db.Column(db.String(20), nullable=False) # client, witness, officer
signature_data = db.Column(db.Text) # Base64 image or digital signature
ip_address = db.Column(db.String(45))
user_agent = db.Column(db.Text)
signed_at = db.Column(db.DateTime, default=datetime.utcnow)

# Relations
user = db.relationship('User', backref='signatures')

class DocumentVersion(db.Model):
__tablename__ = 'document_versions'
__table_args__ = {'schema': 'kredilakay'}

id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.documents.id'), nullable=False)
version_number = db.Column(db.Integer, nullable=False)
file_path = db.Column(db.String(255), nullable=False)
changes = db.Column(JSONB) # {updated_fields: ['amount', 'due_date']}
created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.users.id'))
created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Relations
creator = db.relationship('User', backref='document_versions')

__table_args__ = (
db.UniqueConstraint('document_id', 'version_number', name='uq_document_version'),
)
