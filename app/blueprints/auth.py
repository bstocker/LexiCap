"""Authentification et profil utilisateur."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..forms import LoginForm, ProfileForm
from ..models import LoginEvent, User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    # Aucun compte encore créé : on bascule sur l'assistant de configuration.
    if User.query.count() == 0:
        return redirect(url_for("setup.first_run"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Email ou mot de passe incorrect.", "danger")
        elif not user.active:
            flash("Ce compte est désactivé.", "warning")
        else:
            login_user(user, remember=form.remember.data)
            # Trace la connexion (pour les statistiques d'engagement).
            db.session.add(LoginEvent(user_id=user.id))
            db.session.commit()
            next_page = request.args.get("next")
            # Sécurité : n'autorise que les redirections internes.
            if not next_page or not next_page.startswith("/"):
                next_page = url_for("dashboard.index")
            return redirect(next_page)
    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        if form.password.data:
            current_user.set_password(form.password.data)
            flash("Mot de passe mis à jour.", "success")
        db.session.commit()
        flash("Profil enregistré.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html", form=form)
