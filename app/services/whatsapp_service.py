# KREDILAKAY/app/services/whatsapp_service.py
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import datetime
from app.database import get_db
from app.models import NotificationLog
from config import settings
from typing import Dict, Optional
import logging
import jinja2
import os

class WhatsAppService:
    """Service d'envoi de messages WhatsApp via l'API Twilio"""

    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.whatsapp_number = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
        self.template_loader = jinja2.FileSystemLoader(
            searchpath=os.path.join(settings.TEMPLATES_DIR, "whatsapp")
        )
        self.template_env = jinja2.Environment(loader=self.template_loader)

    def send_template_message(
        self,
        to_number: str,
        template_name: str,
        context: Dict,
        language: str = "fr"
    ) -> Dict:
        """
        Envoie un message WhatsApp basé sur un template Jinja2
        Args:
            to_number: Numéro de téléphone format international (ex: +509XXXXXXXX)
            template_name: Nom du template (sans extension)
            context: Variables pour le template
            language: Langue du message (fr/kreyol)
        Returns:
            Dict: {
                'status': 'sent'|'failed',
                'message_sid': str,
                'error': Optional[str]
            }
        """
        try:
            # Validation du numéro
            if not to_number.startswith("+"):
                to_number = f"+{to_number.lstrip(' ')}"
            whatsapp_to = f"whatsapp:{to_number}"

            # Rendu du template
            template = self._get_template(template_name, language)
            body = template.render(**context)

            # Envoi via Twilio
            message = self.client.messages.create(
                from_=self.whatsapp_number,
                body=body,
                to=whatsapp_to
            )

            # Journalisation
            self._log_notification(
                to_number=to_number,
                template=template_name,
                message_sid=message.sid,
                status="sent",
                body=body,
                context=context
            )

            return {
                'status': 'sent',
                'message_sid': message.sid,
                'body': body
            }

        except TwilioRestException as e:
            error_msg = f"Twilio error: {str(e)}"
            logging.error(error_msg)
            self._log_notification(
                to_number=to_number,
                template=template_name,
                status="failed",
                error=error_msg,
                context=context
            )
            return {
                'status': 'failed',
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logging.error(error_msg)
            return {
                'status': 'failed',
                'error': error_msg
            }

    def _get_template(self, template_name: str, language: str) -> jinja2.Template:
        """Charge le template dans la langue appropriée"""
        template_path = f"{language}/{template_name}.txt"
        return self.template_env.get_template(template_path)

    def _log_notification(
        self,
        to_number: str,
        template: str,
        status: str,
        message_sid: Optional[str] = None,
        body: Optional[str] = None,
        error: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """Journalise la notification dans la base de données"""
        try:
            with get_db() as db:
                log = NotificationLog(
                    id=str(uuid.uuid4()),
                    channel="whatsapp",
                    recipient=to_number,
                    template_used=template,
                    message_sid=message_sid,
                    status=status,
                    body=body,
                    error=error,
                    context=context if context else {},
                    sent_at=datetime.utcnow()
                )
                db.add(log)
                db.commit()
        except Exception as e:
            logging.error(f"Failed to log notification: {str(e)}")

    # Méthodes spécifiques pour KrediLakay
    def send_payment_reminder(
        self,
        to_number: str,
        client_name: str,
        amount_due: Decimal,
        due_date: str,
        loan_id: str,
        language: str = "fr"
    ) -> Dict:
        """Envoie un rappel de paiement personnalisé"""
        return self.send_template_message(
            to_number=to_number,
            template_name="payment_reminder",
            context={
                "client_name": client_name,
                "amount_due": f"{amount_due:.2f}",
                "due_date": due_date,
                "loan_id": loan_id,
                "penalty_note": self._get_penalty_note(language)
            },
            language=language
        )

    def send_contract_notification(
        self,
        to_number: str,
        client_name: str,
        loan_amount: Decimal,
        loan_duration: int,
        language: str = "fr"
    ) -> Dict:
        """Notifie le client qu'un contrat est prêt"""
        return self.send_template_message(
            to_number=to_number,
            template_name="contract_ready",
            context={
                "client_name": client_name,
                "loan_amount": f"{loan_amount:.2f}",
                "loan_duration": loan_duration
            },
            language=language
        )

    def _get_penalty_note(self, language: str) -> str:
        """Retourne la note sur les pénalités selon la langue"""
        notes = {
            "fr": "Après la date d'échéance, une pénalité de 2% par jour sera appliquée.",
            "kreyol": "Apre dat echèans, yon penalite 2% chak jou ap aplike."
        }
        return notes.get(language, notes["fr"])

class WhatsAppTemplateError(Exception):
    """Exception pour les erreurs de templates WhatsApp"""
    pass
