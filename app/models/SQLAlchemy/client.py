from datetime import datetime
from sqlalchemy import (
    Column, String, Date, Integer, Boolean, Text, ForeignKey, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    __table_args__ = (
        {'schema': 'kredilakay'},
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment='ID unique du client'
    )
    first_name = Column(
        String(50),
        nullable=False,
        comment='Prénom du client'
    )
    last_name = Column(
        String(50),
        nullable=False,
        comment='Nom de famille du client'
    )
    email = Column(
        String(120),
        unique=True,
        nullable=False,
        comment='Email principal du client'
    )
    phone = Column(
        String(20),
        unique=True,
        nullable=False,
        comment='Numéro de téléphone principal'
    )
    birth_date = Column(
        Date,
        nullable=False,
        comment='Date de naissance'
    )
    national_id = Column(
        String(30),
        unique=True,
        comment='Numéro d\'identification nationale'
    )
    address = Column(
        JSONB,
        nullable=False,
        server_default='{}',
        comment='Adresse complète au format JSON'
    )
    risk_score = Column(
        Integer,
        default=50,
        comment='Score de risque (0-100)'
    )
    kyc_status = Column(
        String(15),
        default='pending',
        comment='Statut KYC: pending/verified/rejected'
    )
    last_login_at = Column(
        DateTime,
        comment='Dernière connexion'
    )
    created_at = Column(
        DateTime,
        server_default=func.now(),
        comment='Date de création'
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment='Dernière mise à jour'
    )

    # Relations
    loans = relationship(
        "Loan",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    devices = relationship(
        "Device",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Client(id={self.id}, email={self.email})>"


class Device(Base):
    __tablename__ = 'client_devices'
    __table_args__ = (
        {'schema': 'kredilakay'},
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment='ID unique de l\'appareil'
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey('kredilakay.clients.id'),
        nullable=False,
        comment='Référence au client'
    )
    fingerprint = Column(
        String(255),
        nullable=False,
        comment='Empreinte numérique de l\'appareil'
    )
    user_agent = Column(
        Text,
        comment='User-agent du navigateur'
    )
    ip_address = Column(
        INET,
        comment='Adresse IP de connexion'
    )
    last_used = Column(
        DateTime,
        server_default=func.now(),
        comment='Dernière utilisation'
    )
    is_verified = Column(
        Boolean,
        default=False,
        comment='Appareil vérifié'
    )

    # Relation
    client = relationship(
        "Client",
        back_populates="devices"
    )

    def __repr__(self):
        return f"<Device(id={self.id}, client_id={self.client_id})>"
