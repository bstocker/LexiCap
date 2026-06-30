"""Gestion des tâches."""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import TaskForm
from ..models import Subject, Task, TutorialQuestion

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def _subject_choices():
    choices = [(0, "—")]
    choices += [(s.id, s.name) for s in Subject.query.filter_by(active=True).order_by(Subject.name)]
    return choices


def _apply_form(task, form):
    task.title = form.title.data
    task.description = form.description.data
    task.subject_id = form.subject_id.data or None
    task.task_type = form.task_type.data
    task.priority = form.priority.data
    task.due_date = form.due_date.data
    task.estimated_minutes = form.estimated_minutes.data
    task.actual_minutes = form.actual_minutes.data
    # Suit la date de complétion quand le statut passe à « Terminée ».
    if form.status.data == "Terminée" and task.status != "Terminée":
        task.completed_at = datetime.utcnow()
    task.status = form.status.data


@bp.route("/")
@login_required
def index():
    status = request.args.get("status")
    query = Task.query
    if status:
        query = query.filter_by(status=status)
    tasks = query.order_by(Task.due_date.is_(None), Task.due_date).all()
    return render_template("tasks/list.html", tasks=tasks, current_status=status)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = TaskForm()
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        task = Task(created_by=current_user.id, assigned_to=current_user.id)
        _apply_form(task, form)
        db.session.add(task)
        db.session.commit()
        flash("Tâche créée.", "success")
        return redirect(url_for("tasks.index"))
    return render_template("tasks/form.html", form=form, title="Nouvelle tâche")


@bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = db.get_or_404(Task, task_id)
    form = TaskForm(obj=task)
    form.subject_id.choices = _subject_choices()
    if request.method == "GET":
        form.subject_id.data = task.subject_id or 0
    if form.validate_on_submit():
        _apply_form(task, form)
        db.session.commit()
        flash("Tâche mise à jour.", "success")
        return redirect(url_for("tasks.index"))
    return render_template("tasks/form.html", form=form, title="Modifier la tâche")


@bp.route("/<int:task_id>/complete", methods=["POST"])
@login_required
def complete(task_id):
    task = db.get_or_404(Task, task_id)
    task.status = "Terminée"
    task.completed_at = datetime.utcnow()
    db.session.commit()
    flash("Tâche terminée. Bravo !", "success")
    return redirect(request.referrer or url_for("tasks.index"))


@bp.route("/<int:task_id>/block", methods=["POST"])
@login_required
def block(task_id):
    """RG-006 : une tâche bloquée peut générer une question pour le tuteur."""
    task = db.get_or_404(Task, task_id)
    task.status = "Bloquée"
    question = TutorialQuestion(
        question=f"[Tâche bloquée : {task.title}] ",
        subject_id=task.subject_id,
        source_type="Tâche",
        source_id=task.id,
        priority="Haute",
    )
    db.session.add(question)
    db.session.commit()
    flash("Tâche marquée bloquée et question tuteur créée.", "info")
    return redirect(url_for("questions.edit", question_id=question.id))


@bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete(task_id):
    task = db.get_or_404(Task, task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Tâche supprimée.", "info")
    return redirect(url_for("tasks.index"))
