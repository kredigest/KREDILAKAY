from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app import db
import sqlalchemy as sa

class ClientPhoto(db.Model):
    __tablename__ = 'client_photos'
    __table_args__ = {'schema': 'kredilakay'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'))
    client_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.clients.id'), nullable=False)
    filepath = db.Column(db.Text, nullable=False)
    file_hash = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('client_id', 'file_hash', name='unique_client_photo'),
        {'schema': 'kredilakay'}
    )

    def __repr__(self):
        return f'<ClientPhoto {self.filepath}>'
