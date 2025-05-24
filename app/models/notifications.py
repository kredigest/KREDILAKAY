
from datetime import datetime
from enum import Enum
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import event
from .base import BaseModel

class NotificationType(Enum):
    SMS = 'sms'
    EMAIL = 'email'
    PUSH = 'push'
    SYSTEM = 'system'

class NotificationStatus(Enum):
    PENDING = 'pending'
    SENT = 'sent'
    FAILED = 'failed'
    READ = 'read'

class Notification(BaseModel):
    __tablename__ = 'notifications'
    __table_args__ = {'schema': 'kredilakay'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.users.id'), nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    status = db.Column(db.Enum(NotificationStatus), default=NotificationStatus.PENDING)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    metadata = db.Column(JSONB)  # {template_id: '', variables: {}}
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    retry_count = db.Column(db.Integer, default=0)
    channel_data = db.Column(JSONB)  # {sms_provider: '', email_response: ''}

    # Relations
    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.type.value} for user {self.user_id}>'

    def mark_as_sent(self):
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.utcnow()
        return self

    def mark_as_failed(self):
        self.status = NotificationStatus.FAILED
        self.retry_count += 1
        return self

    def to_dict(self):
        return {
            'id': str(self.id),
            'type': self.type.value,
            'status': self.status.value,
            'title': self.title,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'read': bool(self.read_at)
        }

# Event listeners
@event.listens_for(Notification, 'before_insert')
def set_default_metadata(mapper, connection, target):
    if target.metadata is None:
        target.metadata = {
            'template': 'default',
            'variables': {}
        }

class NotificationTemplate(BaseModel):
    __tablename__ = 'notification_templates'
    __table_args__ = {'schema': 'kredilakay'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    name = db.Column(db.String(50), unique=True, nullable=False)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    subject = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    variables = db.Column(JSONB)  # Available template variables
    is_active = db.Column(db.Boolean, default=True)
    version = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f'<NotificationTemplate {self.name} v{self.version}>'
