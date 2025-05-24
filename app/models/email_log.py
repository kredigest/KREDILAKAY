from sqlalchemy import Column, String, Integer, JSON, DateTime
from app.database import Base

class EmailLog(Base):
    __tablename__ = 'email_logs'
    
    id = Column(String(36), primary_key=True)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255))
    template_used = Column(String(100))
    status_code = Column(Integer)
    error_message = Column(String(500))
    context = Column(JSON)
    sent_at = Column(DateTime, default=datetime.utcnow)
