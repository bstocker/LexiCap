"""Administration : gestion des utilisateurs (réservé au rôle admin)."""
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import UserForm
from ..models import User

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.role, User.email).all()
    return render_template("admin/users.html", users=all_users)


@bp.route("/users/new", methods=["GET", "POST"])
@admin_required
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé.", "danger")
        elif not form.password.data:
            flash("Un mot de passe est requis pour créer un compte.", "danger")
        else:
            user = User(
                email=email,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=form.role.data,
                active=form.active.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Utilisateur créé.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html", form=form, title="Nouvel utilisateur")


@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = db.get_or_404(User, user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.email = form.email.data.lower().strip()
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.role = form.role.data
        user.active = form.active.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash("Utilisateur mis à jour.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html", form=form, title="Modifier l'utilisateur")
