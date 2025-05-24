# KREDILAKAY/app/services/client_photo.py
import os
import uuid
from pathlib import Path
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import magic
from werkzeug.utils import secure_filename
from sqlalchemy import text
from app.database import get_db
from config import settings

class ClientPhotoService:
    """Service de gestion des photos clients avec vérification de sécurité"""

    def __init__(self):
        self.storage_path = Path(settings.CLIENT_PHOTOS_DIR)
        self.allowed_mime_types = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/webp': 'webp'
        }
        self.max_size_mb = 5
        self.min_dimensions = (300, 300)

    def save_client_photo(self, file_stream, client_id: str) -> dict:
        """
        Enregistre une photo client avec vérification de sécurité
        Args:
            file_stream: Flux du fichier image
            client_id: ID du client associé
        Returns:
            dict: Métadonnées du fichier sauvegardé
        Raises:
            ValueError: Si l'image est invalide
        """
        # Vérification initiale
        file_bytes = file_stream.read()
        self._validate_image(file_bytes)

        # Traitement de l'image
        processed_image = self._process_image(file_bytes)

        # Génération nom de fichier sécurisé
        filename = self._generate_filename(client_id, file_bytes)

        # Stockage physique
        save_path = self.storage_path / filename
        processed_image.save(save_path, quality=85)

        # Enregistrement en base
        return self._save_to_database(str(save_path), client_id)

    def _validate_image(self, file_bytes: bytes):
        """Valide le fichier image selon les critères de sécurité"""
        # Vérification du type MIME réel
        mime = magic.from_buffer(file_bytes, mime=True)
        if mime not in self.allowed_mime_types:
            raise ValueError(f"Type de fichier non supporté: {mime}")

        # Vérification de la taille
        if len(file_bytes) > self.max_size_mb * 1024 * 1024:
            raise ValueError(f"Taille maximale dépassée ({self.max_size_mb}MB)")

        # Vérification du contenu image
        try:
            with Image.open(BytesIO(file_bytes)) as img:
                if img.size[0] < self.min_dimensions[0] or img.size[1] < self.min_dimensions[1]:
                    raise ValueError(
                        f"Dimensions minimales non respectées: {self.min_dimensions}"
                    )
        except UnidentifiedImageError:
            raise ValueError("Fichier image corrompu ou invalide")

    def _process_image(self, file_bytes: bytes) -> Image:
        """Traite l'image pour le stockage (redimensionnement, format)"""
        with Image.open(BytesIO(file_bytes)) as img:
            # Conversion en RGB (pour les PNG avec alpha)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Redimensionnement proportionnel si trop grand
            if img.size[0] > 1024 or img.size[1] > 1024:
                img.thumbnail((1024, 1024))

            return img

    def _generate_filename(self, client_id: str, file_bytes: bytes) -> str:
        """Génère un nom de fichier sécurisé avec hash"""
        mime = magic.from_buffer(file_bytes, mime=True)
        extension = self.allowed_mime_types.get(mime, 'jpg')
        
        # Hash du contenu pour éviter les collisions
        file_hash = hashlib.sha256(file_bytes).hexdigest()[:16]
        
        return secure_filename(f"client_{client_id}_{file_hash}.{extension}")

    def _save_to_database(self, filepath: str, client_id: str) -> dict:
        """Enregistre les métadonnées en base avec pgcrypto"""
        with get_db() as db:
            # Utilisation de pgcrypto pour le hash
            result = db.execute(
                text("""
                INSERT INTO kredilakay.client_photos 
                (id, client_id, filepath, file_hash)
                VALUES (
                    gen_random_uuid(),
                    :client_id,
                    :filepath,
                    digest(read(:filepath)::bytea, 'sha256')
                )
                RETURNING id, filepath, encode(file_hash, 'hex') as file_hash
                """),
                {
                    'client_id': client_id,
                    'filepath': filepath
                }
            ).fetchone()

            db.commit()
            return {
                'photo_id': result[0],
                'filepath': result[1],
                'file_hash': result[2]
            }

    def get_client_photo(self, photo_id: str):
        """Récupère une photo client avec vérification d'intégrité"""
        with get_db() as db:
            record = db.execute(
                text("""
                SELECT filepath, encode(file_hash, 'hex') as stored_hash
                FROM kredilakay.client_photos
                WHERE id = :photo_id
                """),
                {'photo_id': photo_id}
            ).fetchone()

            if not record:
                raise FileNotFoundError("Photo non trouvée")

            current_hash = hashlib.sha256(Path(record[0]).read_bytes()).hexdigest()
            if current_hash != record[1]:
                raise SecurityError("L'intégrité de la photo a été compromise")

            return record[0]
