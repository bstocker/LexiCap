"""Factory de l'application LexiCap."""
import os
import secrets

import click
from flask import Flask

from config import get_config
from .extensions import db, login_manager, migrate


def create_app(config_class=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class or get_config())

    # S'assure que le dossier instance/ (base SQLite, uploads) existe.
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Clé secrète persistante : si aucune SECRET_KEY n'est fournie par
    # l'environnement, on en génère une et on la conserve dans instance/ pour
    # qu'elle reste stable d'un redémarrage à l'autre (sessions valides).
    _ensure_secret_key(app)

    # Initialisation des extensions.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Enregistrement des blueprints.
    from .blueprints import (
        auth, courses, dashboard, deploy, evaluations, questions,
        reviews, setup, subjects, tasks, td, tutoring, worksheets, admin,
    )
    app.register_blueprint(deploy.bp)
    app.register_blueprint(setup.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(subjects.bp)
    app.register_blueprint(courses.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(td.bp)
    app.register_blueprint(worksheets.bp)
    app.register_blueprint(questions.bp)
    app.register_blueprint(tutoring.bp)
    app.register_blueprint(evaluations.bp)
    app.register_blueprint(reviews.bp)
    app.register_blueprint(admin.bp)

    register_template_helpers(app)
    register_cli(app)

    # Création automatique des tables manquantes au démarrage.
    # Pratique pour un déploiement simple (PythonAnywhere) : aucune commande
    # manuelle n'est nécessaire. Désactivable via AUTO_CREATE_DB=0 si l'on
    # préfère gérer le schéma uniquement avec les migrations Flask-Migrate.
    if os.environ.get("AUTO_CREATE_DB", "1") != "0":
        with app.app_context():
            db.create_all()

    return app


def _ensure_secret_key(app):
    """Garantit une SECRET_KEY stable, générée et stockée si non fournie."""
    weak_defaults = (None, "", "dev-key-a-changer-en-production", "change-me")
    if app.config.get("SECRET_KEY") not in weak_defaults:
        return  # Une vraie clé a été fournie par l'environnement.

    key_path = os.path.join(app.instance_path, "secret_key")
    if os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as fh:
            app.config["SECRET_KEY"] = fh.read().strip()
    else:
        new_key = secrets.token_hex(32)
        with open(key_path, "w", encoding="utf-8") as fh:
            fh.write(new_key)
        app.config["SECRET_KEY"] = new_key


def register_template_helpers(app):
    """Met à disposition des gabarits des constantes et utilitaires communs."""
    from datetime import date

    from . import models as m

    @app.context_processor
    def inject_globals():
        return {
            "today": date.today(),
            "ROLE_LABELS": m.ROLE_LABELS,
            "app_name": "LexiCap",
        }


def register_cli(app):
    """Commandes en ligne de commande utilitaires."""
    from . import models as m

    @app.cli.command("init-db")
    def init_db():
        """Crée les tables de la base de données."""
        db.create_all()
        click.echo("Base de données initialisée.")

    @app.cli.command("create-user")
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option("--role", default="student", type=click.Choice(m.ROLES))
    @click.option("--first-name", default="")
    @click.option("--last-name", default="")
    def create_user(email, password, role, first_name, last_name):
        """Crée un utilisateur (ex: le compte de l'étudiante ou de l'admin)."""
        if m.User.query.filter_by(email=email).first():
            click.echo(f"Un utilisateur avec l'email {email} existe déjà.")
            return
        user = m.User(email=email, role=role, first_name=first_name, last_name=last_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Utilisateur {email} créé avec le rôle {role}.")

    @app.cli.command("seed-subjects")
    def seed_subjects():
        """Ajoute les matières types de L1 Droit (si la table est vide)."""
        if m.Subject.query.first():
            click.echo("Des matières existent déjà, rien à faire.")
            return
        noms = [
            "Introduction au droit", "Droit civil", "Droit constitutionnel",
            "Institutions juridictionnelles", "Histoire du droit",
            "Méthodologie juridique", "Anglais juridique",
            "Relations internationales", "Économie",
        ]
        for nom in noms:
            db.session.add(m.Subject(name=nom, semester="S1", active=True))
        db.session.commit()
        click.echo(f"{len(noms)} matières ajoutées.")
