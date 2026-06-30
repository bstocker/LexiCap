"""Emploi du temps : grille hebdomadaire récurrente + événements de la semaine."""
from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..extensions import db
from ..forms import ScheduleSlotForm
from ..models import (
    Evaluation, ScheduleSlot, Subject, Task, TdSession, WEEKDAYS,
)

bp = Blueprint("schedule", __name__, url_prefix="/schedule")

# Plage horaire affichée et échelle verticale de la grille.
DAY_START_H = 8
DAY_END_H = 20
PX_PER_MIN = 0.8
N_DAYS = 6  # Lundi → Samedi


def _subject_choices():
    choices = [(0, "—")]
    choices += [(s.id, s.name) for s in Subject.query.filter_by(active=True).order_by(Subject.name)]
    return choices


@bp.route("/")
@login_required
def week():
    today = date.today()
    ref = request.args.get("date")
    try:
        ref = date.fromisoformat(ref) if ref else today
    except ValueError:
        ref = today
    monday = ref - timedelta(days=ref.weekday())
    days = [monday + timedelta(days=i) for i in range(N_DAYS)]

    slots = ScheduleSlot.query.all()
    slots_by_day = {i: [] for i in range(N_DAYS)}
    day_start_min = DAY_START_H * 60
    for s in slots:
        if s.day_of_week not in slots_by_day:
            continue
        slots_by_day[s.day_of_week].append({
            "top": (s.start_minutes - day_start_min) * PX_PER_MIN,
            "height": max((s.end_minutes - s.start_minutes) * PX_PER_MIN, 18),
            "label": (s.subject.name if s.subject else s.slot_type),
            "sub": f"{s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}"
                   + (f" · {s.room}" if s.room else ""),
            "type": s.slot_type,
            "color": s.color,
        })

    # Événements datés tombant dans la semaine (TD, évaluations, tâches à échéance).
    end = monday + timedelta(days=N_DAYS - 1)
    events_by_date = {d: [] for d in days}

    def add(d, label, kind):
        if d in events_by_date:
            events_by_date[d].append({"label": label, "kind": kind})

    for td in TdSession.query.filter(TdSession.td_date.between(monday, end)).all():
        add(td.td_date, f"TD : {td.theme}", "td")
    for ev in Evaluation.query.filter(Evaluation.evaluation_date.between(monday, end)).all():
        add(ev.evaluation_date,
            f"{ev.evaluation_type}" + (f" ({ev.subject.name})" if ev.subject else ""), "eval")
    for t in Task.query.filter(
        Task.due_date.between(monday, end), ~Task.status.in_(Task.DONE_STATUSES)
    ).all():
        add(t.due_date, f"Tâche : {t.title}", "task")

    week_days = []
    for i, d in enumerate(days):
        week_days.append({
            "date": d,
            "label": f"{WEEKDAYS[i]} {d.strftime('%d/%m')}",
            "is_today": d == today,
            "slots": sorted(slots_by_day[i], key=lambda x: x["top"]),
            "events": events_by_date[d],
        })

    hours = list(range(DAY_START_H, DAY_END_H + 1))
    grid_height = (DAY_END_H - DAY_START_H) * 60 * PX_PER_MIN

    return render_template(
        "schedule/week.html",
        week_days=week_days, hours=hours, day_start_h=DAY_START_H,
        px_per_min=PX_PER_MIN, grid_height=grid_height,
        prev_date=(monday - timedelta(days=7)).isoformat(),
        next_date=(monday + timedelta(days=7)).isoformat(),
        monday=monday, today=today,
    )


@bp.route("/manage")
@login_required
def manage():
    slots = ScheduleSlot.query.order_by(ScheduleSlot.day_of_week, ScheduleSlot.start_time).all()
    return render_template("schedule/manage.html", slots=slots, weekdays=WEEKDAYS)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = ScheduleSlotForm()
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        slot = ScheduleSlot(
            day_of_week=form.day_of_week.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            subject_id=form.subject_id.data or None,
            slot_type=form.slot_type.data,
            room=form.room.data,
            note=form.note.data,
        )
        db.session.add(slot)
        db.session.commit()
        flash("Créneau ajouté.", "success")
        return redirect(url_for("schedule.manage"))
    return render_template("schedule/form.html", form=form, title="Nouveau créneau")


@bp.route("/<int:slot_id>/edit", methods=["GET", "POST"])
@login_required
def edit(slot_id):
    slot = db.get_or_404(ScheduleSlot, slot_id)
    form = ScheduleSlotForm(obj=slot)
    form.subject_id.choices = _subject_choices()
    if request.method == "GET":
        form.subject_id.data = slot.subject_id or 0
    if form.validate_on_submit():
        slot.day_of_week = form.day_of_week.data
        slot.start_time = form.start_time.data
        slot.end_time = form.end_time.data
        slot.subject_id = form.subject_id.data or None
        slot.slot_type = form.slot_type.data
        slot.room = form.room.data
        slot.note = form.note.data
        db.session.commit()
        flash("Créneau mis à jour.", "success")
        return redirect(url_for("schedule.manage"))
    return render_template("schedule/form.html", form=form, title="Modifier le créneau")


@bp.route("/<int:slot_id>/delete", methods=["POST"])
@login_required
def delete(slot_id):
    slot = db.get_or_404(ScheduleSlot, slot_id)
    db.session.delete(slot)
    db.session.commit()
    flash("Créneau supprimé.", "info")
    return redirect(url_for("schedule.manage"))
