"""Assistant de première connexion.

Tant qu'aucun utilisateur n'existe, /setup permet de créer le premier compte
(administrateur) directement depuis le navigateur — utile pour un déploiement
sur PythonAnywhere sans accès à une console. La route se désactive d'elle-même
dès qu'un compte existe.
"""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_user

from ..extensions import db
from ..forms import FirstAdminForm
from ..models import User

bp = Blueprint("setup", __name__)


@bp.route("/setup", methods=["GET", "POST"])
def first_run():
    # Sécurité : l'assistant n'est accessible que si la base ne contient
    # encore aucun utilisateur.
    if User.query.count() > 0:
        return redirect(url_for("auth.login"))

    form = FirstAdminForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower().strip(),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role="admin",
            active=True,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Compte administrateur créé. Bienvenue sur LexiCap !", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("setup.html", form=form)
