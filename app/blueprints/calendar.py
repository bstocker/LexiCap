"""Vue calendrier mensuelle : TD, évaluations et tâches à échéance."""
import calendar as _cal
from datetime import date

from flask import Blueprint, render_template, request
from flask_login import login_required

from ..models import Evaluation, Task, TdSession

bp = Blueprint("calendar", __name__, url_prefix="/calendar")

MONTH_NAMES = [
    "", "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]
DAY_NAMES = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


@bp.route("/")
@login_required
def month():
    today = date.today()
    year = request.args.get("year", default=today.year, type=int)
    month = request.args.get("month", default=today.month, type=int)
    # Normalise les débordements de mois.
    if month < 1:
        month, year = 12, year - 1
    elif month > 12:
        month, year = 1, year + 1

    # Construit le dictionnaire {date: [événements]} pour le mois affiché.
    events = {}

    def add(d, label, kind):
        if d and d.year == year and d.month == month:
            events.setdefault(d.day, []).append({"label": label, "kind": kind})

    for td in TdSession.query.all():
        add(td.td_date, f"TD : {td.theme}", "td")
    for ev in Evaluation.query.all():
        add(ev.evaluation_date, f"{ev.evaluation_type}"
            + (f" ({ev.subject.name})" if ev.subject else ""), "eval")
    for t in Task.query.filter(~Task.status.in_(Task.DONE_STATUSES)).all():
        add(t.due_date, f"Tâche : {t.title}", "task")

    weeks = _cal.Calendar(firstweekday=0).monthdayscalendar(year, month)

    prev_month = month - 1 or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    return render_template(
        "calendar/month.html",
        year=year, month=month, month_name=MONTH_NAMES[month],
        day_names=DAY_NAMES, weeks=weeks, events=events, today=today,
        prev_year=prev_year, prev_month=prev_month,
        next_year=next_year, next_month=next_month,
    )
