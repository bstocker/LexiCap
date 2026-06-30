"""Fiches de révision."""
from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from ..extensions import db
from ..forms import WorksheetForm
from ..models import Course, Subject, Worksheet

bp = Blueprint("worksheets", __name__, url_prefix="/worksheets")


def _subject_choices():
    return [(s.id, s.name) for s in Subject.query.filter_by(active=True).order_by(Subject.name)]


def _course_choices():
    choices = [(0, "—")]
    choices += [(c.id, f"{c.title} ({c.course_date})")
                for c in Course.query.order_by(Course.course_date.desc())]
    return choices


def _apply_form(ws, form):
    ws.title = form.title.data
    ws.subject_id = form.subject_id.data
    ws.course_id = form.course_id.data or None
    ws.chapter = form.chapter.data
    ws.content_md = form.content_md.data
    ws.status = form.status.data
    ws.mastery_level = int(form.mastery_level.data) if form.mastery_level.data else None
    ws.last_review_date = form.last_review_date.data
    ws.next_review_date = form.next_review_date.data


@bp.route("/")
@login_required
def index():
    worksheets = Worksheet.query.order_by(Worksheet.created_at.desc()).all()
    return render_template("worksheets/list.html", worksheets=worksheets)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = WorksheetForm()
    form.subject_id.choices = _subject_choices()
    form.course_id.choices = _course_choices()
    if form.validate_on_submit():
        ws = Worksheet()
        _apply_form(ws, form)
        db.session.add(ws)
        db.session.commit()
        flash("Fiche créée.", "success")
        return redirect(url_for("worksheets.detail", worksheet_id=ws.id))
    return render_template("worksheets/form.html", form=form, title="Nouvelle fiche")


@bp.route("/<int:worksheet_id>")
@login_required
def detail(worksheet_id):
    ws = db.get_or_404(Worksheet, worksheet_id)
    return render_template("worksheets/detail.html", ws=ws)


@bp.route("/<int:worksheet_id>/edit", methods=["GET", "POST"])
@login_required
def edit(worksheet_id):
    ws = db.get_or_404(Worksheet, worksheet_id)
    form = WorksheetForm(obj=ws)
    form.subject_id.choices = _subject_choices()
    form.course_id.choices = _course_choices()
    if form.validate_on_submit():
        _apply_form(ws, form)
        db.session.commit()
        flash("Fiche mise à jour.", "success")
        return redirect(url_for("worksheets.detail", worksheet_id=ws.id))
    return render_template("worksheets/form.html", form=form, title="Modifier la fiche")


@bp.route("/<int:worksheet_id>/review", methods=["POST"])
@login_required
def review(worksheet_id):
    """Marque la fiche révisée et planifie la prochaine révision (+7 jours)."""
    ws = db.get_or_404(Worksheet, worksheet_id)
    ws.last_review_date = date.today()
    ws.next_review_date = date.today() + timedelta(days=7)
    db.session.commit()
    flash("Fiche révisée. Prochaine révision dans 7 jours.", "success")
    return redirect(url_for("worksheets.detail", worksheet_id=ws.id))
