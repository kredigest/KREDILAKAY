
import os
import boto3
from botocore.exceptions import ClientError
from io import BytesIO
from hashlib import sha256
from flask import current_app
from app.models import db, Document

class PDFStorage:
    def __init__(self):
        self.storage_type = current_app.config['DOCUMENT_STORAGE']

        if self.storage_type == 's3':
            self.client = boto3.client(
                's3',
                aws_access_key_id=current_app.config['AWS_ACCESS_KEY'],
                aws_secret_access_key=current_app.config['AWS_SECRET_KEY'],
                region_name=current_app.config['AWS_REGION']
            )

    def save_document(self, pdf_data, user, document_type, loan_id=None):
        """Stocke le PDF de manière sécurisée"""
        try:
            # Génération d'un nom de fichier unique
            file_hash = sha256(pdf_data).hexdigest()
            filename = f"{user.id}_{document_type}_{file_hash[:16]}.pdf"

            # Stockage selon la configuration
            if self.storage_type == 's3':
                self._save_to_s3(filename, pdf_data)
                filepath = f"s3://{current_app.config['S3_BUCKET']}/{filename}"
            else:
                filepath = self._save_local(filename, pdf_data)

            # Enregistrement en base
            doc = Document(
                user_id=user.id,
                loan_id=loan_id,
                document_type=document_type,
                file_path=filepath,
                file_hash=file_hash,
                storage_type=self.storage_type
            )
            db.session.add(doc)
            db.session.commit()

            return doc
        except Exception as e:
            current_app.logger.error(f"Storage Error: {str(e)}")
            raise

    def _save_to_s3(self, filename, data):
        """Stockage sécurisé sur S3 avec chiffrement"""
        extra_args = {
            'ACL': 'private',
            'ServerSideEncryption': 'AES256',
            'Metadata': {
                'x-amz-meta-secure': 'true'
            }
        }
        self.client.put_object(
            Bucket=current_app.config['S3_BUCKET'],
            Key=filename,
            Body=BytesIO(data),
            **extra_args
        )

    def _save_local(self, filename, data):
        """Stockage local avec protection des permissions"""
        storage_path = current_app.config['LOCAL_STORAGE_PATH']
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, mode=0o750)

        filepath = os.path.join(storage_path, filename)
        with open(filepath, 'wb') as f:
            f.write(data)

        # Protection des permissions
        os.chmod(filepath, 0o640)
        return filepath
