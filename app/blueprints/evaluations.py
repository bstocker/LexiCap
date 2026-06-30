"""Évaluations, devoirs et notes."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import EvaluationForm
from ..models import Evaluation, Subject, Task

bp = Blueprint("evaluations", __name__, url_prefix="/evaluations")


def _subject_choices():
    return [(s.id, s.name) for s in Subject.query.filter_by(active=True).order_by(Subject.name)]


@bp.route("/")
@login_required
def index():
    evals = Evaluation.query.order_by(Evaluation.evaluation_date.desc()).all()
    return render_template("evaluations/list.html", evals=evals)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = EvaluationForm()
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        ev = Evaluation()
        form.populate_obj(ev)
        db.session.add(ev)
        db.session.commit()
        flash("Évaluation créée.", "success")
        return redirect(url_for("evaluations.detail", eval_id=ev.id))
    return render_template("evaluations/form.html", form=form, title="Nouvelle évaluation")


@bp.route("/<int:eval_id>")
@login_required
def detail(eval_id):
    ev = db.get_or_404(Evaluation, eval_id)
    return render_template("evaluations/detail.html", ev=ev)


@bp.route("/<int:eval_id>/edit", methods=["GET", "POST"])
@login_required
def edit(eval_id):
    ev = db.get_or_404(Evaluation, eval_id)
    form = EvaluationForm(obj=ev)
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        form.populate_obj(ev)
        db.session.commit()
        # RG-007 : une note < 10 doit générer une action corrective.
        if ev.grade is not None and ev.grade < 10 and not ev.improvement_action:
            flash("Note inférieure à 10 : pensez à définir une action corrective (RG-007).", "warning")
        flash("Évaluation mise à jour.", "success")
        return redirect(url_for("evaluations.detail", eval_id=ev.id))
    return render_template("evaluations/form.html", form=form, title="Modifier l'évaluation")


@bp.route("/<int:eval_id>/improvement-task", methods=["POST"])
@login_required
def improvement_task(eval_id):
    """Crée une tâche corrective à partir de l'évaluation (RG-007)."""
    ev = db.get_or_404(Evaluation, eval_id)
    task = Task(
        title=ev.improvement_action or f"Action corrective — {ev.subject.name}",
        description=ev.correction_comment,
        subject_id=ev.subject_id,
        task_type="Exercice",
        priority="Haute",
        created_by=current_user.id,
        assigned_to=current_user.id,
    )
    ev.status = "Exploitée"
    db.session.add(task)
    db.session.commit()
    flash("Action corrective créée.", "success")
    return redirect(url_for("tasks.edit", task_id=task.id))
