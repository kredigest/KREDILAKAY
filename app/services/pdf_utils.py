# KREDILAKAY/app/services/pdf_utils.py
from io import BytesIO
from PyPDF2 import PdfWriter, PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.lib import colors
import qrcode
import hashlib
from datetime import datetime
from pathlib import Path
from app.database import get_db
from config import settings
from typing import Optional, Tuple
import logging

class PDFGenerator:
    """Générateur de documents PDF sécurisés pour KrediLakay"""

    def __init__(self):
        self.styles = self._init_styles()
        self.logo_path = Path(settings.PDF_LOGO_PATH)
        self.font_dir = Path(settings.FONT_DIR)
        self.watermark_text = settings.WATERMARK_TEXT

    def _init_styles(self):
        """Initialise les styles ReportLab"""
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Kreyol',
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='Title',
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=1,
            spaceAfter=12
        ))
        return styles

    def generate_contract(
        self,
        loan_data: dict,
        client_data: dict,
        signature_img: Optional[bytes] = None
    ) -> BytesIO:
        """
        Génère un contrat PDF professionnel
        Args:
            loan_data: Données du prêt (montant, durée, etc.)
            client_data: Info client (nom, photo, etc.)
            signature_img: Signature numérique (bytes)
        Returns:
            BytesIO: Flux PDF en mémoire
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            title=f"Contrat KrediLakay {loan_data['id']}",
            author="Système KrediLakay"
        )

        story = []
        self._add_cover_page(story, client_data, loan_data)
        self._add_terms(story, loan_data)
        
        if signature_img:
            self._add_signature_page(story, signature_img)

        doc.build(story)
        pdf_bytes = self._finalize_pdf(buffer, loan_data['id'])
        return pdf_bytes

    def _add_cover_page(self, story, client_data, loan_data):
        """Ajoute une page de couverture professionnelle"""
        # Logo et en-tête
        logo = Image(self.logo_path, width=2*inch, height=1*inch)
        story.append(logo)
        story.append(Spacer(1, 0.5*inch))

        # Titre
        title = Paragraph("CONTRAT DE PRÊT", self.styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))

        # Photo client si disponible
        if client_data.get('photo_path'):
            client_photo = Image(client_data['photo_path'], width=1.5*inch, height=1.5*inch)
            story.append(client_photo)
            story.append(Spacer(1, 0.2*inch))

        # Info client
        client_info = [
            f"<b>Client:</b> {client_data['full_name']}",
            f"<b>ID:</b> {client_data['id']}",
            f"<b>Téléphone:</b> {client_data['phone']}",
            f"<b>Adresse:</b> {client_data['address']}"
        ]
        for line in client_info:
            story.append(Paragraph(line, self.styles['Kreyol']))

        # Info prêt
        story.append(Spacer(1, 0.3*inch))
        loan_info = [
            f"<b>Montant:</b> {loan_data['amount']} HTG",
            f"<b>Durée:</b> {loan_data['duration_days']} jours",
            f"<b>Taux journalier:</b> {loan_data['daily_interest_rate']*100:.2f}%",
            f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}"
        ]
        for line in loan_info:
            story.append(Paragraph(line, self.styles['Kreyol']))

        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("<i>Veuillez lire attentivement les termes ci-dessous</i>", self.styles['Kreyol']))
        story.append(PageBreak())

    def _add_terms(self, story, loan_data):
        """Ajoute les termes et conditions du contrat"""
        # Clause 1
        terms = [
            "<b>1. Montant du Prêt:</b> Le prêteur accorde un prêt de {} HTG au client.".format(loan_data['amount']),
            Spacer(1, 0.2*inch),
            "<b>2. Durée:</b> Le prêt doit être remboursé dans un délai de {} jours.".format(loan_data['duration_days']),
            Spacer(1, 0.2*inch),
            "<b>3. Intérêts:</b> Taux d'intérêt journalier de {}%.".format(loan_data['daily_interest_rate']*100),
            Spacer(1, 0.2*inch),
            "<b>4. Pénalités:</b> En cas de retard, une pénalité de 2% par jour sera appliquée.",
            Spacer(1, 0.2*inch),
            "<b>5. Droit Haïtien:</b> Ce contrat est régi par les lois de la République d'Haïti."
        ]

        for item in terms:
            if isinstance(item, str):
                story.append(Paragraph(item, self.styles['Kreyol']))
            else:
                story.append(item)

    def _add_signature_page(self, story, signature_img):
        """Ajoute une page de signature"""
        story.append(PageBreak())
        story.append(Paragraph("<b>Signature du Client</b>", self.styles['Title']))
        story.append(Spacer(1, 0.5*inch))

        # Image de la signature
        sig_img = Image(BytesIO(signature_img), width=3*inch, height=1*inch)
        story.append(sig_img)
        story.append(Spacer(1, 0.2*inch))

        # Ligne de signature
        story.append(Paragraph("_"*50, self.styles['Kreyol']))
        story.append(Paragraph("<i>Signature du client</i>", self.styles['Kreyol']))

    def _finalize_pdf(self, buffer, loan_id) -> BytesIO:
        """Finalise le PDF avec sécurité et métadonnées"""
        buffer.seek(0)
        pdf_reader = PdfReader(buffer)
        pdf_writer = PdfWriter()

        # Ajout du filigrane et métadonnées
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

        # Métadonnées
        pdf_writer.add_metadata({
            '/Title': f'Contrat KrediLakay {loan_id}',
            '/Author': 'Système KrediLakay',
            '/Creator': 'KrediLakay PDF Generator',
            '/Producer': 'ReportLab + PyPDF2',
            '/CreationDate': datetime.now().strftime("D:%Y%m%d%H%M%S")
        })

        # Ajout du QR Code sécurisé
        self._add_qr_code(pdf_writer, loan_id)

        # Finalisation
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer

    def _add_qr_code(self, pdf_writer, loan_id):
        """Ajoute un QR Code de vérification"""
        verification_url = f"{settings.BASE_URL}/verify-contract?loan={loan_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=2
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convertir en image ReportLab
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Ajouter au PDF
        from reportlab.pdfgen import canvas
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.drawImage(qr_buffer, 450, 50, width=100, height=100)
        can.save()

        packet.seek(0)
        qr_pdf = PdfReader(packet)
        for page in pdf_writer.pages:
            page.merge_page(qr_pdf.pages[0])

class PDFSecurity:
    """Classe utilitaire pour la sécurité des PDF"""

    @staticmethod
    def generate_document_hash(pdf_bytes: bytes) -> str:
        """Génère un hash SHA-256 du contenu PDF"""
        return hashlib.sha256(pdf_bytes).hexdigest()

    @staticmethod
    def add_digital_signature(pdf_bytes: bytes, signature_data: dict) -> bytes:
        """Ajoute une signature numérique au PDF"""
        # Implémentation utilisant endesive
        from endesive import pdf
        import datetime

        date = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
        date = date.strftime("D:%Y%m%d%H%M%S+00'00'")

        dct = {
            "sigflags": 3,
            "contact": signature_data['contact'],
            "location": signature_data['location'],
            "signingdate": date.encode(),
            "reason": signature_data['reason'],
        }

        # Configuration PKI (à adapter avec votre certificat)
        p12 = signature_data['p12_certificate']
        passwd = signature_data['cert_password']
        p12data = open(p12, "rb").read()

        return pdf.cms.sign(
            pdf_bytes,
            dct,
            p12data,
            passwd,
            "sha256"
        )

    @staticmethod
    def verify_signature(pdf_bytes: bytes) -> dict:
        """Vérifie la signature d'un PDF"""
        from endesive import pdf

        results = []
        for (name, doc, revision, obj) in pdf.verify(pdf_bytes):
            results.append({
                'signer': name,
                'valid': doc.verify(obj),
                'timestamp': obj.get('signingdate', b'').decode(),
                'reason': obj.get('reason', b'').decode()
            })

        return {
            'is_signed': len(results) > 0,
            'signatures': results,
            'all_valid': all(r['valid'] for r in results)
        }
