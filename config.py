"""Configuration de l'application LexiCap.

Les paramètres sensibles (SECRET_KEY, DATABASE_URL) doivent être fournis par
des variables d'environnement en production. Des valeurs par défaut adaptées au
développement local sont prévues pour pouvoir lancer l'application immédiatement.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Charge un éventuel fichier .env à la racine du projet.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # Clé secrète : OBLIGATOIREMENT redéfinie en production via l'environnement.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-a-changer-en-production")

    # Base de données : SQLite par défaut (simple, suffisant pour un usage familial).
    # En production on peut fournir DATABASE_URL (ex: PostgreSQL).
    _default_sqlite = f"sqlite:///{BASE_DIR / 'instance' / 'lexicap.sqlite'}"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", _default_sqlite)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads (préparé pour une future gestion documentaire).
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "instance" / "uploads"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))

    # Sécurité des sessions / cookies.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


def get_config():
    """Renvoie la classe de configuration selon FLASK_ENV."""
    env = os.environ.get("FLASK_ENV", "development").lower()
    if env in ("production", "prod"):
        return ProductionConfig
    return Config
