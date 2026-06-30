"""Séances de tutorat."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import TutoringForm
from ..models import TutoringSession

bp = Blueprint("tutoring", __name__, url_prefix="/tutoring")


@bp.route("/")
@login_required
def index():
    sessions = TutoringSession.query.order_by(TutoringSession.session_date.desc()).all()
    return render_template("tutoring/list.html", sessions=sessions)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = TutoringForm()
    if form.validate_on_submit():
        session = TutoringSession(tutor_id=current_user.id)
        form.populate_obj(session)
        db.session.add(session)
        db.session.commit()
        flash("Séance enregistrée.", "success")
        return redirect(url_for("tutoring.detail", session_id=session.id))
    return render_template("tutoring/form.html", form=form, title="Nouvelle séance")


@bp.route("/<int:session_id>")
@login_required
def detail(session_id):
    session = db.get_or_404(TutoringSession, session_id)
    return render_template("tutoring/detail.html", session=session)


@bp.route("/<int:session_id>/edit", methods=["GET", "POST"])
@login_required
def edit(session_id):
    session = db.get_or_404(TutoringSession, session_id)
    form = TutoringForm(obj=session)
    if form.validate_on_submit():
        form.populate_obj(session)
        db.session.commit()
        flash("Séance mise à jour.", "success")
        return redirect(url_for("tutoring.detail", session_id=session.id))
    return render_template("tutoring/form.html", form=form, title="Modifier la séance")
