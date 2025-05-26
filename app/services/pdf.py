import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from flask import current_app
import os

class PDFService:
    @staticmethod
    def _register_fonts():
        fonts_path = os.path.join(current_app.root_path, 'static/fonts')
        try:
            pdfmetrics.registerFont(TTFont('Roboto', os.path.join(fonts_path, 'Roboto-Regular.ttf')))
            pdfmetrics.registerFont(TTFont('Roboto-Bold', os.path.join(fonts_path, 'Roboto-Bold.ttf')))
        except:
            current_app.logger.warning("Polices non chargées, fallback en cours")

    @classmethod
    def generate_loan_contract(cls, contract_data):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        cls._register_fonts()
        styles = getSampleStyleSheet()
        styles['Normal'].fontName = 'Roboto'
        styles['Title'].fontName = 'Roboto-Bold'
        
        story = []
        story.append(Paragraph("CONTRAT DE PRÊT", styles['Title']))
        story.append(Spacer(1, 0.5*inch))
        content = f"""
        Entre <b>Kredilakay</b> et <b>{contract_data['client_name']}</b>,<br/><br/>
        Montant : {contract_data['loan_amount']:,} HTG<br/>
        Durée : {contract_data['duration']} mois<br/>
        Taux : {contract_data['interest_rate']}%<br/>
        Réf. Contrat : {contract_data['contract_id']}
        """
        story.append(Paragraph(content, styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("Signatures :", styles['Normal']))
        doc.build(story)
        return buffer.getvalue()
