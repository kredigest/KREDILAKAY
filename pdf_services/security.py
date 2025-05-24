from endesive import pdf
from OpenSSL import crypto
import datetime
import os
from flask import current_app

class DigitalSigner:
    def __init__(self):
        self.cert_path = current_app.config['SIGNING_CERT']
        self.key_path = current_app.config['SIGNING_KEY']
        self.password = current_app.config['SIGNING_PASSWORD']

    def sign(self, pdf_writer):
        """Applique une signature numérique PAdES"""
        if not all([self.cert_path, self.key_path, self.password]):
            return pdf_writer

        try:
            # Préparation des données de signature
            date = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
            date = date.strftime("D:%Y%m%d%H%M%S+00'00'")

            # Lecture du certificat et clé
            with open(self.cert_path, 'rb') as f:
                cert = f.read()
            with open(self.key_path, 'rb') as f:
                key = f.read()

            # Création du dictionnaire de signature
            dct = {
                "sigflags": 3,
                "contact": current_app.config['COMPANY_EMAIL'],
                "location": current_app.config['COMPANY_LOCATION'],
                "signingdate": date,
                "reason": "KrediGest Document Certification",
                "signature": "KrediGest",
                "signaturebox": (0, 0, 100, 50),
            }

            # Création d'un buffer pour le PDF
            buffer = io.BytesIO()
            pdf_writer.write(buffer)
            buffer.seek(0)

            # Application de la signature
            data = pdf.cms.sign(
                buffer.read(),
                dct,
                key,
                cert,
                [],
                "sha256",
                self.password
            )

            # Réécriture du PDF signé
            signed_pdf = io.BytesIO(data)
            pdf_reader = PdfReader(signed_pdf)
            pdf_writer = PdfWriter()

            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

            return pdf_writer

        except Exception as e:
            current_app.logger.error(f"Signing Error: {str(e)}")
            return pdf_writer
