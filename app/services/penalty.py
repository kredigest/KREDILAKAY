from decimal import Decimal
from datetime import datetime

class PenaltyCalculator:
    def __init__(self, loan):
        self.loan = loan
        self.daily_rate = Decimal('0.02')  # 2% par jour
    
    @property
    def days_late(self):
        if not self.loan.start_date:
            return 0
        due_date = self.loan.start_date + timedelta(days=self.loan.duration_days)
        return max((datetime.utcnow().date() - due_date).days, 0)
    
    def calculate_total(self):
        return self.loan.total_due * self.daily_rate * self.days_late
# KREDILAKAY/app/services/pdf_watermark.py
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color, red, black
from reportlab.lib.utils import ImageReader
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
from pathlib import Path
from config import settings
import logging

class PDFWatermarker:
    """Service d'ajout de filigranes avec calcul automatique de pénalités"""

    def __init__(self):
        self.penalty_rate = Decimal('0.02')  # 2% par jour
        self.watermark_config = {
            'font_name': 'Helvetica-Bold',
            'font_size': 12,
            'color': (0.9, 0, 0, 0.7),  # Rouge transparent pour les pénalités
            'angle': 0,
            'spacing': 100
        }

    def apply_penalty_watermark(
        self,
        pdf_bytes: bytes,
        loan_data: dict,
        as_of_date: datetime = None
    ) -> bytes:
        """
        Applique un filigrane avec mention de pénalité si en retard
        Args:
            pdf_bytes: Contenu PDF original
            loan_data: {
                'due_date': datetime,
                'total_amount': Decimal,
                'loan_id': str
            }
            as_of_date: Date de calcul (par défaut aujourd'hui)
        Returns:
            bytes: PDF avec filigrane de pénalité si applicable
        """
        as_of_date = as_of_date or datetime.now()
        penalty_info = self._calculate_penalty(
            loan_data['due_date'],
            loan_data['total_amount'],
            as_of_date
        )

        if not penalty_info['has_penalty']:
            return pdf_bytes  # Pas de filigrane si pas de retard

        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        pdf_writer = PdfWriter()

        watermark_page = self._create_penalty_watermark(penalty_info)

        for page in pdf_reader.pages:
            page.merge_page(watermark_page)
            pdf_writer.add_page(page)

        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        return output_buffer.getvalue()

    def _calculate_penalty(
        self,
        due_date: datetime,
        total_amount: Decimal,
        as_of_date: datetime
    ) -> dict:
        """Calcule les pénalités de retard"""
        if as_of_date <= due_date:
            return {
                'has_penalty': False,
                'penalty_amount': Decimal('0'),
                'days_late': 0
            }

        days_late = (as_of_date - due_date).days
        penalty_amount = (total_amount * self.penalty_rate * days_late).quantize(Decimal('0.01'))

        return {
            'has_penalty': True,
            'penalty_amount': penalty_amount,
            'days_late': days_late,
            'total_with_penalty': (total_amount + penalty_amount).quantize(Decimal('0.01')),
            'due_date': due_date.strftime('%d/%m/%Y'),
            'calculation_date': as_of_date.strftime('%d/%m/%Y')
        }

    def _create_penalty_watermark(self, penalty_info: dict) -> PdfReader:
        """Crée une page de filigrane avec les détails de pénalité"""
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Style pour le texte de pénalité
        can.setFont(self.watermark_config['font_name'], self.watermark_config['font_size'])
        can.setFillColorRGB(*self.watermark_config['color'][:3], alpha=self.watermark_config['color'][3])

        # Position en bas à droite de chaque page
        text_x = 400
        text_y = 30

        penalty_text = (
            f"PÉNALITÉ DE RETARD: {penalty_info['days_late']} jour(s) "
            f"({self.penalty_rate*100}%/jour) | "
            f"+{penalty_info['penalty_amount']} HTG | "
            f"TOTAL DÛ: {penalty_info['total_with_penalty']} HTG"
        )

        can.drawString(text_x, text_y, penalty_text)

        # Ajout des dates importantes
        date_text = (
            f"Échéance: {penalty_info['due_date']} | "
            f"Calculé le: {penalty_info['calculation_date']}"
        )
        can.drawString(text_x, text_y - 20, date_text)

        can.save()
        packet.seek(0)
        return PdfReader(packet).pages[0]

    def generate_security_stamp(self, pdf_bytes: bytes) -> dict:
        """
        Génère un cachet de sécurité avec hash du document
        Args:
            pdf_bytes: Contenu PDF
        Returns:
            dict: {
                'hash': str,
                'algorithm': str,
                'generated_at': str
            }
        """
        doc_hash = hashlib.sha256(pdf_bytes).hexdigest()
        return {
            'hash': doc_hash,
            'algorithm': 'SHA-256',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

class PenaltyWatermarkError(Exception):
    """Exception personnalisée pour les erreurs de filigrane"""
    pass
