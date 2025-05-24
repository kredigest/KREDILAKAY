import os
import logging
from io import BytesIO
from datetime import datetime
from xhtml2pdf import pisa
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from app import app
from .watermark import add_watermark
from .security import apply_security_features

logger = logging.getLogger(__name__)

class PDFGenerationError(Exception):
    pass

class PDFGenerator:
    TEMPLATES_DIR = os.path.join(app.root_path, 'templates/pdf')
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_from_html(self, template_name, context, output_path=None):
        """
        Génère un PDF à partir d'un template HTML
        Args:
            template_name: Nom du fichier template (sans extension)
            context: Dictionnaire de données pour le template
            output_path: Chemin de sortie (None pour retourner bytes)
        Returns:
            bytes ou None si output_path est spécifié
        """
        try:
            # Rendu du template HTML
            html_content = self._render_template(template_name, context)
            
            # Conversion en PDF
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_buffer,
                encoding='UTF-8',
                link_callback=self._handle_resources
            )
            
            if pisa_status.err:
                raise PDFGenerationError("Erreur de conversion HTML vers PDF")
            
            # Ajout des fonctionnalités de sécurité
            secured_pdf = self._apply_security(pdf_buffer, context)
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(secured_pdf)
                return None
            return secured_pdf
            
        except Exception as e:
            logger.error(f"Erreur génération PDF: {str(e)}")
            raise

    def generate_from_reportlab(self, elements, output_path=None):
        """
        Génère un PDF avec ReportLab (pour documents complexes)
        Args:
            elements: Liste d'éléments Platypus
            output_path: Chemin de sortie
        Returns:
            bytes ou None
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        doc.build(elements)
        
        secured_pdf = apply_security_features(buffer.getvalue())
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(secured_pdf)
            return None
        return secured_pdf

    def _render_template(self, template_name, context):
        """Rendu du template HTML avec Jinja2"""
        from flask import render_template
        return render_template(f'pdf/{template_name}.html', **context)

    def _handle_resources(self, uri, rel):
        """Gestion des ressources externes (images, CSS)"""
        static_path = os.path.join(app.root_path, 'static')
        if uri.startswith('static/'):
            path = os.path.join(static_path, uri.replace('static/', ''))
            return path
        return None

    def _apply_security(self, pdf_buffer, context):
        """Applique les fonctionnalités de sécurité"""
        pdf_buffer.seek(0)
        pdf_reader = PdfReader(pdf_buffer)
        pdf_writer = PdfWriter()
        
        # Copie des pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Filigrane conditionnel
        if context.get('status') == 'approved':
            add_watermark(pdf_writer, "APPROUVÉ")
        elif context.get('status') == 'rejected':
            add_watermark(pdf_writer, "REJETÉ")
        
        # Sécurité documentaire
        apply_security_features(pdf_writer)
        
        # Finalisation
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        return output_buffer.getvalue()

class ContractPDFGenerator(PDFGenerator):
    def generate_loan_contract(self, loan, client, output_path=None):
        """Génère un contrat de prêt"""
        context = {
            'loan': loan,
            'client': client,
            'company': app.config['COMPANY_INFO'],
            'generated_at': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'status': 'draft'
        }
        return self.generate_from_html('loan_contract', context, output_path)

class ReceiptPDFGenerator(PDFGenerator):
    def generate_payment_receipt(self, payment, output_path=None):
        """Génère un reçu de paiement"""
        context = {
            'payment': payment,
            'client': payment.loan.client,
            'company': app.config['COMPANY_INFO'],
            'generated_at': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'status': 'approved'
        }
        return self.generate_from_html('payment_receipt', context, output_path)
