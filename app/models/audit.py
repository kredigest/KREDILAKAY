from sqlalchemy import Column, String, DateTime, JSON
from app.database import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(String(36), primary_key=True)
    event_type = Column(String(50))
    provider = Column(String(50))
    status = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)
