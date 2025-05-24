# KREDILAKAY/app/services/__init__.py
from flask import current_app
from .auth import AuthService
from .pdf import PDFService
from .payment import PaymentProcessor
from .risk import RiskAssessment
from .storage import DocumentStorage
from .notifications import NotificationManager
from .penalty import PenaltyCalculator

def init_services(app):
    """Initialise tous les services avec la configuration de l'application"""
    services = {
        'auth': AuthService(app.config['JWT_SECRET']),
        'pdf': PDFService(
            app.config['PDF_TEMPLATES_DIR'],
            app.config['FONTS_DIR']
        ),
        'payment': PaymentProcessor(
            app.config['PAYMENT_PROVIDERS'],
            app.config['COMMISSION_RATES']
        ),
        'risk': RiskAssessment(
            app.config['RISK_MODEL_PATH'],
            app.config['RISK_THRESHOLD']
        ),
        'storage': DocumentStorage(
            app.config['DOCUMENT_STORAGE_URI'],
            app.config['STORAGE_ENCRYPTION_KEY']
        ),
        'notifications': NotificationManager(
            twilio_sid=app.config['TWILIO_SID'],
            twilio_token=app.config['TWILIO_TOKEN'],
            sendgrid_key=app.config['SENDGRID_KEY']
        ),
        'penalty': PenaltyCalculator(
            daily_rate=app.config['PENALTY_RATE'],
            grace_period=app.config['GRACE_PERIOD_DAYS']
        )
    }
    
    # Make services available on app context
    app.extensions['services'] = services
    
    # Initialize async tasks if needed
    if app.config['ENABLE_ASYNC']:
        from .tasks import init_task_queue
        init_task_queue(app)

    return services

def get_service(service_name):
    """Récupère un service par son nom depuis le contexte actuel"""
    return current_app.extensions['services'].get(service_name)
