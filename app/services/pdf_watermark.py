# KREDILAKAY/app/services/pdf_watermark.py
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color, lightgrey
from reportlab.lib.utils import ImageReader
from typing import Union, Optional
import hashlib
from pathlib import Path
from config import settings
import logging

class PDFWatermarker:
    """Service d'ajout de filigranes sécurisés aux documents PDF"""

    def __init__(self):
        self.watermark_config = {
            'text': settings.WATERMARK_TEXT,
            'font_name': 'Helvetica-Bold',
            'font_size': 40,
            'color': (0.9, 0.9, 0.9, 0.6),  # RGBA (transparent light grey)
            'angle': 45,
            'spacing': 200
        }
        self.logo_path = Path(settings.SECURITY_LOGO_PATH)

    def apply_watermark(
        self,
        pdf_bytes: bytes,
        watermark_type: str = 'text',
        custom_text: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bytes:
        """
        Applique un filigrane sécurisé au PDF
        Args:
            pdf_bytes: Contenu PDF original
            watermark_type: 'text' ou 'logo'
            custom_text: Texte personnalisé pour le filigrane
            user_id: ID de l'utilisateur pour traçabilité
        Returns:
            bytes: PDF avec filigrane
        """
        try:
            pdf_reader = PdfReader(BytesIO(pdf_bytes))
            pdf_writer = PdfWriter()

            watermark_page = self._create_watermark_page(
                watermark_type=watermark_type,
                custom_text=custom_text,
                user_id=user_id
            )

            for page in pdf_reader.pages:
                # Fusionner le filigrane avec chaque page
                page.merge_page(watermark_page)
                pdf_writer.add_page(page)

            # Ajouter les métadonnées de sécurité
            self._add_security_metadata(pdf_writer, user_id)

            output_buffer = BytesIO()
            pdf_writer.write(output_buffer)
            return output_buffer.getvalue()

        except Exception as e:
            logging.error(f"Erreur d'application du filigrane: {str(e)}")
            raise PDFWatermarkError(f"Échec de l'application du filigrane: {str(e)}")

    def _create_watermark_page(
        self,
        watermark_type: str,
        custom_text: Optional[str],
        user_id: Optional[str]
    ) -> PdfReader:
        """Crée une page de filigrane selon le type demandé"""
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        if watermark_type == 'logo':
            self._apply_logo_watermark(can)
        else:
            text = custom_text if custom_text else self.watermark_config['text']
            if user_id:
                text += f" (UID:{user_id})"
            self._apply_text_watermark(can, text)

        can.save()
        packet.seek(0)
        return PdfReader(packet).pages[0]

    def _apply_text_watermark(self, can: canvas.Canvas, text: str):
        """Applique un filigrane textuel"""
        width, height = letter
        can.setFont(
            self.watermark_config['font_name'],
            self.watermark_config['font_size']
        )
        can.setFillColorRGB(*self.watermark_config['color'][:3], alpha=self.watermark_config['color'][3])

        # Appliquer le texte en diagonale répété
        can.saveState()
        can.translate(width / 2, height / 2)
        can.rotate(self.watermark_config['angle'])

        for i in range(-5, 6):
            for j in range(-5, 6):
                can.drawString(
                    i * self.watermark_config['spacing'],
                    j * self.watermark_config['spacing'],
                    text
                )

        can.restoreState()

    def _apply_logo_watermark(self, can: canvas.Canvas):
        """Applique un filigrane avec logo de sécurité"""
        if not self.logo_path.exists():
            raise FileNotFoundError(f"Logo de sécurité introuvable: {self.logo_path}")

        logo = ImageReader(self.logo_path)
        logo_width, logo_height = logo.getSize()
        aspect = logo_height / float(logo_width)
        width = 200
        height = width * aspect

        # Positionner au centre semi-transparent
        can.setFillAlpha(0.2)
        can.drawImage(
            logo,
            (letter[0] - width) / 2,
            (letter[1] - height) / 2,
            width=width,
            height=height,
            mask='auto'
        )
        can.setFillAlpha(1)

    def _add_security_metadata(self, pdf_writer: PdfWriter, user_id: Optional[str]):
        """Ajoute des métadonnées de sécurité"""
        metadata = {
            '/Title': 'Document sécurisé KrediLakay',
            '/Author': 'Système KrediLakay',
            '/Creator': 'PDFWatermarker',
            '/Producer': 'KrediLakay Security',
            '/Watermarked': 'True',
            '/WatermarkType': 'Security'
        }

        if user_id:
            metadata['/WatermarkedBy'] = user_id

        pdf_writer.add_metadata(metadata)

    def generate_tamper_evident_seal(self, pdf_bytes: bytes) -> dict:
        """
        Génère un sceau d'intégrité pour le document
        Returns:
            dict: {'hash': sha256, 'pages': count, 'size': bytes}
        """
        doc_hash = hashlib.sha256(pdf_bytes).hexdigest()
        reader = PdfReader(BytesIO(pdf_bytes))
        
        return {
            'hash': doc_hash,
            'pages': len(reader.pages),
            'size': len(pdf_bytes),
            'algorithm': 'SHA-256'
        }

class PDFWatermarkError(Exception):
    """Exception personnalisée pour les erreurs de filigrane"""
    pass

class SecuritySeal:
    """Gestion des sceaux de sécurité pour documents sensibles"""

    @staticmethod
    def create_seal(pdf_bytes: bytes, secret: str) -> str:
        """
        Crée un sceau cryptographique pour le document
        Args:
            pdf_bytes: Contenu du PDF
            secret: Clé secrète partagée
        Returns:
            str: Sceau HMAC
        """
        hmac_obj = hmac.new(
            secret.encode('utf-8'),
            pdf_bytes,
            hashlib.sha256
        )
        return hmac_obj.hexdigest()

    @staticmethod
    def verify_seal(pdf_bytes: bytes, seal: str, secret: str) -> bool:
        """
        Vérifie l'intégrité d'un document scellé
        Args:
            pdf_bytes: Contenu du PDF
            seal: Sceau à vérifier
            secret: Clé secrète partagée
        Returns:
            bool: True si le sceau est valide
        """
        expected_seal = SecuritySeal.create_seal(pdf_bytes, secret)
        return hmac.compare_digest(expected_seal, seal)

