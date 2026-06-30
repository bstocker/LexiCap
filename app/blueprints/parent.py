"""Tableau de bord « parent » : vue d'ensemble avec graphiques + engagement.

Toutes les données sont agrégées à partir des tables existantes. Le suivi des
connexions s'appuie sur la table login_events alimentée à chaque connexion.
"""
from collections import OrderedDict
from datetime import date, timedelta

from flask import Blueprint, render_template
from flask_login import login_required

from ..models import (
    Course, Document, Evaluation, LoginEvent, TASK_STATUSES, Task,
    TdSession, User, WeeklyReview, Worksheet,
)

bp = Blueprint("parent", __name__, url_prefix="/parent")


def _week_start(d):
    """Lundi de la semaine de la date d."""
    return d - timedelta(days=d.weekday())


def _last_week_starts(n=8):
    monday = _week_start(date.today())
    return [monday - timedelta(weeks=i) for i in range(n - 1, -1, -1)]


def _bucket_by_week(dates, n=8):
    """Compte des dates par semaine sur les n dernières semaines."""
    weeks = _last_week_starts(n)
    counts = OrderedDict((w, 0) for w in weeks)
    first = weeks[0]
    for d in dates:
        if d is None:
            continue
        ws = _week_start(d)
        if ws in counts:
            counts[ws] += 1
        elif ws < first:
            continue
    return counts


def _gather():
    today = date.today()

    # --- Tâches : à faire vs réalisé ---
    tasks = Task.query.all()
    tasks_by_status = {s: 0 for s in TASK_STATUSES}
    for t in tasks:
        tasks_by_status[t.status] = tasks_by_status.get(t.status, 0) + 1
    overdue = sum(1 for t in tasks if t.is_overdue)

    # Tâches terminées par semaine (8 dernières semaines)
    done_dates = [t.completed_at.date() for t in tasks if t.completed_at]
    done_per_week = _bucket_by_week(done_dates)

    # --- Cours / TD / Fiches ---
    courses = Course.query.all()
    courses_reviewed = sum(1 for c in courses if c.reviewed)
    tds = TdSession.query.all()
    tds_ready = sum(1 for td in tds if td.is_ready)
    worksheets = Worksheet.query.all()
    ws_validated = sum(1 for w in worksheets if w.status == "Validée")

    # --- Évaluations : progression des notes ---
    evals = (
        Evaluation.query.filter(Evaluation.grade.isnot(None))
        .order_by(Evaluation.evaluation_date)
        .all()
    )
    grades = [
        {"date": e.evaluation_date.isoformat(),
         "grade": e.grade,
         "subject": e.subject.name if e.subject else "",
         "type": e.evaluation_type}
        for e in evals
    ]
    avg_grade = round(sum(e.grade for e in evals) / len(evals), 2) if evals else None
    submitted = Evaluation.query.filter(Evaluation.status.in_(["Passée", "Corrigée", "Exploitée"])).count()

    # --- Bilans hebdomadaires : moral / charge / fatigue ---
    reviews = WeeklyReview.query.order_by(WeeklyReview.week_date).all()
    morale = [
        {"date": r.week_date.isoformat(),
         "confidence": r.confidence,
         "load": r.perceived_load,
         "fatigue": r.fatigue}
        for r in reviews
    ]

    # --- Engagement : connexions ---
    student = User.query.filter_by(role="student").first()
    login_rows = LoginEvent.query
    if student:
        login_rows = login_rows.filter_by(user_id=student.id)
    login_dates = [le.created_at.date() for le in login_rows.all()]
    logins_per_week = _bucket_by_week(login_dates)
    last_login = None
    if student:
        last = (
            LoginEvent.query.filter_by(user_id=student.id)
            .order_by(LoginEvent.created_at.desc())
            .first()
        )
        last_login = last.created_at if last else None
    days_since_login = (date.today() - last_login.date()).days if last_login else None
    logins_this_week = logins_per_week.get(_week_start(today), 0)

    return {
        "tasks_by_status": tasks_by_status,
        "overdue": overdue,
        "done_per_week": OrderedDict((w.isoformat(), v) for w, v in done_per_week.items()),
        "courses_total": len(courses),
        "courses_reviewed": courses_reviewed,
        "tds_total": len(tds),
        "tds_ready": tds_ready,
        "ws_total": len(worksheets),
        "ws_validated": ws_validated,
        "grades": grades,
        "avg_grade": avg_grade,
        "submitted": submitted,
        "morale": morale,
        "logins_per_week": OrderedDict((w.isoformat(), v) for w, v in logins_per_week.items()),
        "last_login": last_login,
        "days_since_login": days_since_login,
        "logins_this_week": logins_this_week,
        "documents_count": Document.query.count(),
        "student": student,
    }


@bp.route("/")
@login_required
def index():
    return render_template("parent/dashboard.html", **_gather())
