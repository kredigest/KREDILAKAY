from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase

# Convention de nommage pour les contraintes PostgreSQL
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

class BaseModel(DeclarativeBase):
    """Base abstraite pour tous les modèles KrediLakay"""

    metadata = MetaData(naming_convention=naming_convention, schema="kredilakay")

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + 's'

    @declared_attr
    def __table_args__(cls):
        return {'schema': 'kredilakay'}

    def to_dict(self):
        """Convertit le modèle en dictionnaire"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Instance SQLAlchemy configurée
db = SQLAlchemy(
    model_class=BaseModel,
    engine_options={
        'pool_size': 10,
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'connect_args': {
            'connect_timeout': 5,
            'application_name': 'kredilakay_app'
        }
    }
)

def init_db(app):
    """Initialise la base de données avec l'application Flask"""
    db.init_app(app)
    with app.app_context():
        # Crée les tables si elles n'existent pas
        db.reflect()
        db.create_all()
