"""Questions pour le tuteur."""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import AnswerForm, QuestionForm
from ..models import Subject, Task, TutorialQuestion

bp = Blueprint("questions", __name__, url_prefix="/questions")


def _subject_choices():
    choices = [(0, "—")]
    choices += [(s.id, s.name) for s in Subject.query.filter_by(active=True).order_by(Subject.name)]
    return choices


@bp.route("/")
@login_required
def index():
    questions = TutorialQuestion.query.order_by(TutorialQuestion.created_at.desc()).all()
    return render_template("questions/list.html", questions=questions)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = QuestionForm()
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        q = TutorialQuestion(
            question=form.question.data,
            subject_id=form.subject_id.data or None,
            question_type=form.question_type.data,
            priority=form.priority.data,
            status=form.status.data,
        )
        db.session.add(q)
        db.session.commit()
        flash("Question créée.", "success")
        return redirect(url_for("questions.index"))
    return render_template("questions/form.html", form=form, title="Nouvelle question")


@bp.route("/<int:question_id>", methods=["GET", "POST"])
@login_required
def detail(question_id):
    q = db.get_or_404(TutorialQuestion, question_id)
    answer_form = AnswerForm(obj=q)
    # Seul le tuteur (ou l'admin) répond aux questions.
    if answer_form.validate_on_submit() and (current_user.is_tutor or current_user.is_admin):
        q.tutor_answer = answer_form.tutor_answer.data
        q.action_text = answer_form.action_text.data
        q.answered_at = datetime.utcnow()
        if q.status in ("À poser", "Posée"):
            q.status = "Posée"
        db.session.commit()
        flash("Réponse enregistrée.", "success")
        return redirect(url_for("questions.detail", question_id=q.id))
    return render_template("questions/detail.html", q=q, answer_form=answer_form)


@bp.route("/<int:question_id>/edit", methods=["GET", "POST"])
@login_required
def edit(question_id):
    q = db.get_or_404(TutorialQuestion, question_id)
    form = QuestionForm(obj=q)
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        q.question = form.question.data
        q.subject_id = form.subject_id.data or None
        q.question_type = form.question_type.data
        q.priority = form.priority.data
        q.status = form.status.data
        db.session.commit()
        flash("Question mise à jour.", "success")
        return redirect(url_for("questions.detail", question_id=q.id))
    if q.subject_id is None:
        form.subject_id.data = 0
    return render_template("questions/form.html", form=form, title="Modifier la question")


@bp.route("/<int:question_id>/close", methods=["POST"])
@login_required
def close(question_id):
    q = db.get_or_404(TutorialQuestion, question_id)
    q.status = "Clôturée"
    db.session.commit()
    flash("Question clôturée.", "info")
    return redirect(url_for("questions.index"))


@bp.route("/<int:question_id>/create-task", methods=["POST"])
@login_required
def create_task(question_id):
    q = db.get_or_404(TutorialQuestion, question_id)
    task = Task(
        title=q.action_text or f"Suite à la question : {q.question[:60]}",
        description=q.tutor_answer,
        subject_id=q.subject_id,
        task_type="Tutorat",
        priority="Moyenne",
        created_by=current_user.id,
        assigned_to=current_user.id,
    )
    q.status = "Transformée en tâche"
    db.session.add(task)
    db.session.commit()
    flash("Tâche créée à partir de la question.", "success")
    return redirect(url_for("tasks.edit", task_id=task.id))
