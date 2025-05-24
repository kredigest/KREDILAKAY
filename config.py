import os
from datetime import timedelta
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

class Config:
    """Configuration de base"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'votre_cle_secrete_ici')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/kredigest')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Paramètres d'application
    APP_NAME = "KREDITAKAY"
    APP_VERSION = "2.1.0"
    SUPPORTED_LANGUAGES = ['fr', 'ht', 'en']
    
    # Configuration des fichiers
    UPLOAD_FOLDER = os.path.join(os.path.dirname(_file_), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Paramètres de sécurité
    PASSWORD_RESET_EXPIRY = 24  # Heures
    MAX_LOGIN_ATTEMPTS = 5
    
    # Configuration des logs
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'kredigest.log'

class ProductionConfig(Config):
    """Configuration pour la production"""
    ENV = 'production'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('PROD_DATABASE_URL')
    
    # Configuration SMTP
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    ENV = 'development'
    DEBUG = True
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration active
config = {
    'production': ProductionConfig,
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    
    'default': DevelopmentConfig
}
class Settings:
    JWT_SECRET = "votre_clé_secrète_complexe"  # Générer via: openssl rand -hex 32
    JWT_ALGORITHM = "HS256"
    MFA_VALIDITY_WINDOW = 1  # en minutes
class Settings:
    # Clés secrètes pour les fournisseurs
    NATCOM_SECRET = "votre_cle_natcom"
    DIGICEL_SECRET = "votre_cle_digicel"
    UNIBANK_SECRET = "votre_cle_unibank"
    
    # Configuration des webhooks
    WEBHOOK_TIMEOUT = 5  # seconds
class Settings:
    # Services de base
    JWT_SECRET = "votre_clé_jwt_secrète"
    PDF_TEMPLATES_DIR = "/app/templates/contracts"
    FONTS_DIR = "/app/static/fonts"
    
    # Paiements
    PAYMENT_PROVIDERS = {
        'natcom': {
            'api_key': "votre_api_key",
            'commission': 0.015  # 1.5%
        },
        'digicel': {
            'api_key': "votre_api_key", 
            'commission': 0.02   # 2%
        }
    }
    
    # Stockage
    DOCUMENT_STORAGE_URI = "s3://kredilakay-documents"
    STORAGE_ENCRYPTION_KEY = "votre_clé_de_chiffrement"
    
    # Notifications
    TWILIO_SID = "votre_sid_twilio"
    TWILIO_TOKEN = "votre_token_twilio"
    SENDGRID_KEY = "votre_clé_sendgrid"
    
    # Calcul des risques
    RISK_MODEL_PATH = "/models/risk_scoring.pkl"
    RISK_THRESHOLD = 0.7
    
    # Pénalités
    PENALTY_RATE = 0.02  # 2% par jour
    GRACE_PERIOD_DAYS = 5

class Settings:
    SENDGRID_API_KEY = "votre_clé_sendgrid"
    NOREPLY_EMAIL = "noreply@kredilakay.ht"
    EMAIL_TEMPLATES_DIR = "/app/templates/emails"
    LATE_PENALTY_RATE = 0.02  # 2% par jour
class Settings:
    BASE_INTEREST_RATE = "0.15"  # 15% de base
    PENALTY_RATE = "0.02"        # 2% par jour de retard
    GRACE_PERIOD_DAYS = 5        # Délai de grâce avant pénalités
class Settings:
    PDF_LOGO_PATH = "/app/static/images/logo_kredilakay.png"
    FONT_DIR = "/app/static/fonts"
    WATERMARK_TEXT = "KREDILAKAY DOCUMENT OFFICIEL"
    BASE_URL = "https://app.kredilakay.ht"

