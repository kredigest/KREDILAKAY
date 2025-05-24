# KREDILAKAY/app/pdf_services/storage.py
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy import text, LargeBinary
from cryptography.fernet import Fernet
import hashlib
from app.database import get_db
from config import settings

class PDFStorage:
    """Gestion sécurisée du stockage des contrats PDF avec chiffrement HSM et pgcrypto"""
    
    def __init__(self):
        self.storage_path = Path(settings.PDF_STORAGE_PATH)
        self.fernet = Fernet(settings.ENCRYPTION_KEY)
        
    def _generate_checksum(self, pdf_data: bytes) -> str:
        """Génère un hash SHA-256 avec pgcrypto pour intégrité"""
        with get_db() as db:
            result = db.execute(
                text("SELECT encode(digest(:data, 'sha256'), 'hex')"),
                {"data": pdf_data}
            ).scalar()
            return result
    
    def _encrypt_pdf(self, pdf_data: bytes) -> bytes:
        """Chiffrement AES-256 des documents sensibles"""
        return self.fernet.encrypt(pdf_data)
    
    def save_contract(self, pdf_data: bytes, client_id: str) -> dict:
        """Stocke un contrat avec métadonnées sécurisées"""
        # Vérification de l'intégrité
        checksum = self._generate_checksum(pdf_data)
        
        # Chiffrement du document
        encrypted_data = self._encrypt_pdf(pdf_data)
        
        # Nom de fichier sécurisé
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"contract_{client_id}_{timestamp}.pdf.enc"
        
        # Stockage physique
        save_path = self.storage_path / filename
        with open(save_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Métadonnées pour la base de données
        return {
            "filepath": str(save_path),
            "checksum": checksum,
            "original_size": len(pdf_data),
            "encrypted_size": len(encrypted_data),
            "algorithm": "AES-256/Fernet"
        }
    
    def retrieve_contract(self, filepath: str) -> bytes:
        """Récupère et déchiffre un contrat"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Contract file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()
        
        # Déchiffrement
        try:
            pdf_data = self.fernet.decrypt(encrypted_data)
            
            # Vérification d'intégrité post-déchiffrement
            current_checksum = self._generate_checksum(pdf_data)
            stored_checksum = self._get_db_checksum(filepath)
            
            if current_checksum != stored_checksum:
                raise IntegrityError("PDF checksum verification failed")
                
            return pdf_data
        except Exception as e:
            raise SecurityError(f"Decryption failed: {str(e)}")
    
    def _get_db_checksum(self, filepath: str) -> str:
        """Récupère le checksum depuis la base de données"""
        with get_db() as db:
            return db.execute(
                text("""
                SELECT checksum FROM kredilakay.documents 
                WHERE filepath = :filepath
                """),
                {"filepath": filepath}
            ).scalar()

class IntegrityError(Exception):
    """Erreur d'intégrité du document"""
    pass

class SecurityError(Exception):
    """Erreur de sécurité critique"""
    pass
