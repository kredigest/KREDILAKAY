from flask import current_app
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from io import BytesIO
import hashlib
import datetime
from PyPDF2 import PdfReader, PdfWriter
from app.models import AuditLog

class PDFGenerator:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(current_app.config['PDF_TEMPLATE_DIR']),
            autoescape=True
        )

    def generate_pdf(self, template_name, context, user):
        try:
            template = self.env.get_template(f"{template_name}.html")
            html_content = template.render(**context)

            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_buffer,
                encoding='UTF-8',
                link_callback=self._handle_links
            )

            if pisa_status.err:
                raise PDFGenerationError("Échec de la conversion PDF")

            final_pdf = self._add_security_features(
                pdf_buffer,
                user=user,
                document_type=template_name
            )

            AuditLog.log_event(
                user_id=user.id,
                event_type='document',
                action='pdf_generated',
                details={
                    'type': template_name,
                    'context_keys': list(context.keys()),
                    'pdf_size': len(final_pdf),
                    'checksum': hashlib.sha256(final_pdf).hexdigest()
                }
            )

            return final_pdf

        except Exception as e:
            current_app.logger.error(f"PDF Generation Error: {str(e)}")
            raise

    def _add_security_features(self, pdf_buffer, user, document_type):
        pdf_buffer.seek(0)
        pdf_reader = PdfReader(pdf_buffer)
        pdf_writer = PdfWriter()

        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

        metadata = {
            '/Title': f"KrediGest - {document_type}",
            '/Author': 'KrediGest System',
            '/Creator': 'KrediGest PDF Engine',
            '/Producer': 'PyPDF2/xhtml2pdf',
            '/CreationDate': datetime.datetime.now().strftime("D:%Y%m%d%H%M%S"),
            '/Subject': f"Document {document_type} pour {user.email}",
            '/SecurityPolicy': 'AES-256',
            '/UserID': str(user.id)
        }

        pdf_writer.add_metadata(metadata)

        if document_type == 'payment':
            self._add_watermark(pdf_writer, "VALIDÉ")

        if current_app.config['PDF_SIGNING_ENABLED']:
            from .security import DigitalSigner
            signer = DigitalSigner()
            pdf_writer = signer.sign(pdf_writer)

        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        return output_buffer.getvalue()
