from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app import db, login_manager

class UserRole(Enum):
    ADMIN = 'admin'
    AGENT = 'agent'
    CLIENT = 'client'
    AUDITOR = 'auditor'

class UserStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    PENDING = 'pending'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'kredilakay'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.CLIENT)
    status = db.Column(db.Enum(UserStatus), default=UserStatus.PENDING)
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    failed_login_attempts = db.Column(db.Integer, default=0)
    metadata = db.Column(JSONB)  # {avatar: "", preferences: {}}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    clients = db.relationship('Client', backref='account_manager', lazy='dynamic')
    loans_processed = db.relationship('Loan', backref='processing_officer', lazy='dynamic')
    signatures = db.relationship('DocumentSignature', backref='signer', lazy='dynamic')
    devices = db.relationship('UserDevice', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def is_active(self):
        return self.status == UserStatus.ACTIVE

    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value,
            'status': self.status.value
        }

class UserDevice(db.Model):
    __tablename__ = 'user_devices'
    __table_args__ = {'schema': 'kredilakay'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('kredilakay.users.id'), nullable=False)
    device_id = db.Column(db.String(255), nullable=False)  # FingerprintJS ID
    device_name = db.Column(db.String(100))
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    is_trusted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Device {self.device_id} for user {self.user_id}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
