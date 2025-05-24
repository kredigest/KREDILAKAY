from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from app.database import Base

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(String(36), primary_key=True)
    loan_id = Column(String(36), ForeignKey('loans.id'))
    document_type = Column(String(50))
    content = Column(Text)  # Stockage base64 ou chemin fichier
    is_signed = Column(Boolean, default=False)
    signed_version = Column(String(255))
    signed_at = Column(DateTime)
