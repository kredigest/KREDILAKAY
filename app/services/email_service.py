# KREDILAKAY/app/services/email_service.py
import os
import logging
from pathlib import Path
from typing import Dict, Optional
from jinja2 import Environment, FileSystemLoader
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
from app.database import get_db
from app.models import EmailLog
from config import settings
from datetime import datetime

class EmailService:
    """Service d'envoi d'emails transactionnels avec SendGrid et templates Jinja2"""

    def __init__(self):
        self.client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        self.template_env = Environment(
            loader=FileSystemLoader(settings.EMAIL_TEMPLATES_DIR),
            autoescape=True
        )
        self.sender_email = settings.NOREPLY_EMAIL
        self.sender_name = "KrediLakay No-Reply"

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict,
        attachments: Optional[list] = None,
        category: str = "transactional"
    ) -> bool:
        """
        Envoie un email avec template dynamique
        Args:
            to_email: Email du destinataire
            subject: Sujet de l'email
            template_name: Nom du template (sans extension)
            context: Variables pour le template
            attachments: Liste de fichiers joints
            category: Catégorie pour le suivi
        Returns:
            bool: True si l'envoi a réussi
        """
        try:
            # Rendu du template
            html_content = self._render_template(template_name, context)
            text_content = self._render_template(f"{template_name}.txt", context)

            # Construction du message
            message = Mail(
                from_email=(self.sender_email, self.sender_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            message.add_category(category)

            # Gestion des pièces jointes
            if attachments:
                for attachment in attachments:
                    self._attach_file(message, **attachment)

            # Envoi et journalisation
            response = self.client.send(message)
            self._log_email(
                to_email=to_email,
                subject=subject,
                template=template_name,
                status_code=response.status_code,
                context=context
            )

            return response.status_code in [200, 202]
        except Exception as e:
            logging.error(f"Erreur d'envoi d'email: {str(e)}")
            self._log_email(
                to_email=to_email,
                subject=subject,
                template=template_name,
                status_code=500,
                error_message=str(e),
                context=context
            )
            return False

    def _render_template(self, template_name: str, context: Dict) -> str:
        """Rend un template Jinja2 avec le contexte fourni"""
        template_path = f"{template_name}.html"
        template = self.template_env.get_template(template_path)
        return template.render(**context)

    def _attach_file(self, message: Mail, file_path: str, filename: str, mime_type: str):
        """Attache un fichier à l'email"""
        with open(file_path, 'rb') as f:
            data = f.read()

        encoded = base64.b64encode(data).decode()
        attachment = Attachment(
            FileContent(encoded),
            FileName(filename),
            FileType(mime_type),
            Disposition('attachment')
        )
        message.add_attachment(attachment)

    def _log_email(
        self,
        to_email: str,
        subject: str,
        template: str,
        status_code: int,
        error_message: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """Journalise l'envoi d'email dans la base de données"""
        with get_db() as db:
            log = EmailLog(
                id=str(uuid.uuid4()),
                recipient=to_email,
                subject=subject,
                template_used=template,
                status_code=status_code,
                error_message=error_message,
                context=context if context else {},
                sent_at=datetime.utcnow()
            )
            db.add(log)
            db.commit()

    # Méthodes spécifiques pour KrediLakay
    def send_contract_email(self, client_email: str, contract_path: str, client_name: str) -> bool:
        """Envoie un contrat par email au client"""
        return self.send_email(
            to_email=client_email,
            subject=f"Votre contrat KrediLakay - {datetime.now().strftime('%d/%m/%Y')}",
            template_name="contract_notification",
            context={
                "client_name": client_name,
                "current_date": datetime.now().strftime("%d %B %Y")
            },
            attachments=[{
                "file_path": contract_path,
                "filename": f"Contrat_KrediLakay_{client_name}.pdf",
                "mime_type": "application/pdf"
            }],
            category="contract"
        )

    def send_payment_reminder(self, client_email: str, amount_due: float, due_date: str) -> bool:
        """Envoie un rappel de paiement"""
        return self.send_email(
            to_email=client_email,
            subject=f"Rappel de paiement - {due_date}",
            template_name="payment_reminder",
            context={
                "amount_due": amount_due,
                "due_date": due_date,
                "penalty_rate": settings.LATE_PENALTY_RATE
            },
            category="reminder"
        )
