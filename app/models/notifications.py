
from datetime import datetime
from enum import Enum
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import event

class NotificationChannel(Enum):
    WHATSAPP = 'whatsapp'
    EMAIL = 'email'

class NotificationStatus(Enum):
    PENDING = 'pending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    FAILED = 'failed'
    READ = 'read'

class Notification(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = {'schema': 'kredilakay'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.users.id'), nullable=False)
    channel = db.Column(db.Enum(NotificationChannel), nullable=False)
    status = db.Column(db.Enum(NotificationStatus), default=NotificationStatus.PENDING)
    subject = db.Column(db.String(100))  # Pour les emails
    content = db.Column(db.Text, nullable=False)
    recipient = db.Column(db.String(150), nullable=False)  # Email ou numéro WhatsApp
    template_id = db.Column(db.String(50))  # Référence au template
    metadata = db.Column(JSONB)  # Variables dynamiques
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    delivery_confirmations = db.Column(JSONB)  # {whatsapp: {status: '', timestamp: ''}, email: {}}
    retry_count = db.Column(db.Integer, default=0)

    # Relations
    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.channel.value} to {self.recipient}>'

    def mark_as_sent(self):
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.utcnow()
        return self

    def add_delivery_confirmation(self, provider, data):
        if not self.delivery_confirmations:
            self.delivery_confirmations = {}
        self.delivery_confirmations[provider] = data
        return self

class NotificationTemplate(db.Model):
    __tablename__ = 'notification_templates'
    __table_args__ = {'schema': 'kredilakay'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    name = db.Column(db.String(50), unique=True, nullable=False)
    channel = db.Column(db.Enum(NotificationChannel), nullable=False)
    content = db.Column(db.Text, nullable=False)
    variables = db.Column(JSONB)  # Variables disponibles
    whatsapp_template = db.Column(JSONB)  # {name: "", namespace: ""}
    email_config = db.Column(JSONB)  # {subject: "", sender: ""}
    is_active = db.Column(db.Boolean, default=True)

    def get_formatted_content(self, variables):
        """Formatte le contenu avec les variables"""
        return self.content.format(**variables)

# Event listeners
@event.listens_for(Notification, 'before_insert')
def set_default_metadata(mapper, connection, target):
    if target.metadata is None:
        target.metadata = {}

