"""Tableau de bord hebdomadaire : vue de synthèse et alertes."""
from datetime import date, timedelta

from flask import Blueprint, render_template
from flask_login import login_required

from ..models import (
    Course, Evaluation, Task, TdSession, TutorialQuestion, Worksheet,
)

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@bp.route("/dashboard")
@login_required
def index():
    today = date.today()
    soon = today + timedelta(days=2)

    # Tâches urgentes (échéance dans les 48h) et tâches en retard.
    open_tasks = Task.query.filter(~Task.status.in_(Task.DONE_STATUSES)).all()
    urgent_tasks = [
        t for t in open_tasks
        if t.due_date and today <= t.due_date <= soon
    ]
    overdue_tasks = [t for t in open_tasks if t.is_overdue]

    # Cours non relus après 48h (RG-001).
    courses_to_review = [
        c for c in Course.query.filter_by(reviewed=False).all() if c.is_overdue_review
    ]

    # TD urgents à moins de 3 jours (RG-002).
    upcoming_td = [
        td for td in TdSession.query.order_by(TdSession.td_date).all() if td.is_urgent
    ]

    # Fiches à revoir (RG-004 + répétition espacée).
    worksheets_to_review = [
        w for w in Worksheet.query.all() if w.needs_review
    ]

    # Questions tuteur ouvertes.
    open_questions = [
        q for q in TutorialQuestion.query.order_by(TutorialQuestion.priority.desc()).all()
        if q.is_open
    ]

    # Prochaines évaluations à moins de 10 jours (RG-005).
    upcoming_evals = [
        e for e in Evaluation.query.order_by(Evaluation.evaluation_date).all()
        if e.is_upcoming
    ]

    return render_template(
        "dashboard.html",
        urgent_tasks=urgent_tasks,
        overdue_tasks=overdue_tasks,
        courses_to_review=courses_to_review,
        upcoming_td=upcoming_td,
        worksheets_to_review=worksheets_to_review,
        open_questions=open_questions,
        upcoming_evals=upcoming_evals,
    )
