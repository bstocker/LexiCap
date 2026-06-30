"""Préparation des TD (travaux dirigés)."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from ..extensions import db
from ..forms import TdForm
from ..models import Subject, TdSession, TutorialQuestion

bp = Blueprint("td", __name__, url_prefix="/td")


def _subject_choices():
    return [(s.id, s.name) for s in Subject.query.filter_by(active=True).order_by(Subject.name)]


@bp.route("/")
@login_required
def index():
    sessions = TdSession.query.order_by(TdSession.td_date).all()
    return render_template("td/list.html", sessions=sessions)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = TdForm()
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        td = TdSession()
        form.populate_obj(td)
        db.session.add(td)
        db.session.commit()
        flash("TD ajouté.", "success")
        return redirect(url_for("td.detail", td_id=td.id))
    return render_template("td/form.html", form=form, title="Nouveau TD")


@bp.route("/<int:td_id>")
@login_required
def detail(td_id):
    td = db.get_or_404(TdSession, td_id)
    return render_template("td/detail.html", td=td)


@bp.route("/<int:td_id>/edit", methods=["GET", "POST"])
@login_required
def edit(td_id):
    td = db.get_or_404(TdSession, td_id)
    form = TdForm(obj=td)
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        form.populate_obj(td)
        db.session.commit()
        flash("TD mis à jour.", "success")
        return redirect(url_for("td.detail", td_id=td.id))
    return render_template("td/form.html", form=form, title="Modifier le TD")


@bp.route("/<int:td_id>/create-question", methods=["POST"])
@login_required
def create_question(td_id):
    td = db.get_or_404(TdSession, td_id)
    question = TutorialQuestion(
        question=f"[À propos du TD : {td.theme}] ",
        subject_id=td.subject_id,
        source_type="TD",
        source_id=td.id,
    )
    db.session.add(question)
    db.session.commit()
    flash("Question pour le tuteur créée.", "success")
    return redirect(url_for("questions.edit", question_id=question.id))
