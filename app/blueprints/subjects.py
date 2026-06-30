"""Gestion des matières."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from ..extensions import db
from ..forms import SubjectForm
from ..models import Subject

bp = Blueprint("subjects", __name__, url_prefix="/subjects")


@bp.route("/")
@login_required
def index():
    subjects = Subject.query.order_by(Subject.active.desc(), Subject.name).all()
    return render_template("subjects/list.html", subjects=subjects)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject()
        form.populate_obj(subject)
        db.session.add(subject)
        db.session.commit()
        flash("Matière créée.", "success")
        return redirect(url_for("subjects.detail", subject_id=subject.id))
    return render_template("subjects/form.html", form=form, title="Nouvelle matière")


@bp.route("/<int:subject_id>")
@login_required
def detail(subject_id):
    subject = db.get_or_404(Subject, subject_id)
    open_tasks = [t for t in subject.tasks if not t.is_done]
    return render_template("subjects/detail.html", subject=subject, open_tasks=open_tasks)


@bp.route("/<int:subject_id>/edit", methods=["GET", "POST"])
@login_required
def edit(subject_id):
    subject = db.get_or_404(Subject, subject_id)
    form = SubjectForm(obj=subject)
    if form.validate_on_submit():
        form.populate_obj(subject)
        db.session.commit()
        flash("Matière mise à jour.", "success")
        return redirect(url_for("subjects.detail", subject_id=subject.id))
    return render_template("subjects/form.html", form=form, title="Modifier la matière")


@bp.route("/seed", methods=["POST"])
@login_required
def seed():
    """Ajoute les matières types de L1 Droit (si aucune n'existe encore)."""
    if Subject.query.first():
        flash("Des matières existent déjà.", "info")
        return redirect(url_for("subjects.index"))
    noms = [
        "Introduction au droit", "Droit civil", "Droit constitutionnel",
        "Institutions juridictionnelles", "Histoire du droit",
        "Méthodologie juridique", "Anglais juridique",
        "Relations internationales", "Économie",
    ]
    for nom in noms:
        db.session.add(Subject(name=nom, semester="S1", active=True))
    db.session.commit()
    flash(f"{len(noms)} matières types ajoutées.", "success")
    return redirect(url_for("subjects.index"))


@bp.route("/<int:subject_id>/archive", methods=["POST"])
@login_required
def archive(subject_id):
    subject = db.get_or_404(Subject, subject_id)
    subject.active = not subject.active
    db.session.commit()
    flash("Matière archivée." if not subject.active else "Matière réactivée.", "info")
    return redirect(url_for("subjects.index"))
