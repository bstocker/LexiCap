"""Emploi du temps : grille hebdomadaire récurrente + événements de la semaine."""
from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from flask_login import current_user

from ..extensions import db
from ..forms import ScheduleSlotForm
from ..models import (
    Course, Evaluation, ScheduleSlot, Subject, Task, TdSession, WEEKDAYS,
    get_setting, set_setting,
)

bp = Blueprint("schedule", __name__, url_prefix="/schedule")

# Plage horaire affichée et échelle verticale de la grille.
DAY_START_H = 8
DAY_END_H = 20
PX_PER_MIN = 0.8


def _show_saturday():
    return get_setting("show_saturday", "1") != "0"


def _parse_date(value, fallback=None):
    try:
        return date.fromisoformat(value) if value else fallback
    except (TypeError, ValueError):
        return fallback


def _subject_choices():
    choices = [(0, "—")]
    choices += [(s.id, s.name) for s in Subject.query.filter_by(active=True).order_by(Subject.name)]
    return choices


@bp.route("/")
@login_required
def week():
    today = date.today()
    ref = _parse_date(request.args.get("date"), today)
    monday = ref - timedelta(days=ref.weekday())
    n_days = 6 if _show_saturday() else 5
    days = [monday + timedelta(days=i) for i in range(n_days)]

    slots = ScheduleSlot.query.all()
    slots_by_day = {i: [] for i in range(n_days)}
    day_start_min = DAY_START_H * 60
    for s in slots:
        if s.day_of_week not in slots_by_day:
            continue
        slots_by_day[s.day_of_week].append({
            "id": s.id,
            "top": (s.start_minutes - day_start_min) * PX_PER_MIN,
            "height": max((s.end_minutes - s.start_minutes) * PX_PER_MIN, 18),
            "label": (s.subject.name if s.subject else s.slot_type),
            "sub": f"{s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}"
                   + (f" · {s.room}" if s.room else ""),
            "type": s.slot_type,
            "color": s.color,
        })

    # Événements datés tombant dans la semaine (TD, évaluations, tâches à échéance).
    end = monday + timedelta(days=n_days - 1)
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
        monday=monday, today=today, show_saturday=_show_saturday(),
    )


@bp.route("/toggle-saturday", methods=["POST"])
@login_required
def toggle_saturday():
    set_setting("show_saturday", "0" if _show_saturday() else "1")
    return redirect(request.referrer or url_for("schedule.week"))


@bp.route("/slot/<int:slot_id>/actions")
@login_required
def slot_actions(slot_id):
    """Petite page d'actions pour un créneau à une date donnée."""
    slot = db.get_or_404(ScheduleSlot, slot_id)
    day = _parse_date(request.args.get("date"), date.today())
    fr_days = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    day_label = f"{fr_days[day.weekday()]} {day.strftime('%d/%m/%Y')}"
    return render_template("schedule/slot_actions.html", slot=slot, day=day, day_label=day_label)


@bp.route("/slot/<int:slot_id>/create-course", methods=["POST"])
@login_required
def create_course(slot_id):
    slot = db.get_or_404(ScheduleSlot, slot_id)
    day = _parse_date(request.form.get("date"), date.today())
    if not slot.subject_id:
        flash("Ce créneau n'a pas de matière : impossible de créer une séance de cours.", "warning")
        return redirect(url_for("schedule.slot_actions", slot_id=slot.id, date=day.isoformat()))
    course_type = slot.slot_type if slot.slot_type in ("CM", "TD") else "CM"
    course = Course(
        subject_id=slot.subject_id,
        title=slot.subject.name,
        course_date=day,
        course_type=course_type,
    )
    db.session.add(course)
    db.session.commit()
    flash("Séance de cours créée — complétez-la si besoin.", "success")
    return redirect(url_for("courses.edit", course_id=course.id))


@bp.route("/slot/<int:slot_id>/create-task", methods=["POST"])
@login_required
def create_task(slot_id):
    slot = db.get_or_404(ScheduleSlot, slot_id)
    day = _parse_date(request.form.get("date"), date.today())
    label = slot.subject.name if slot.subject else slot.slot_type
    type_map = {"TD": "TD", "Révision": "Révision"}
    task = Task(
        title=f"Préparer {label} ({day.strftime('%d/%m')})",
        subject_id=slot.subject_id,
        task_type=type_map.get(slot.slot_type, "Relecture"),
        priority="Moyenne",
        due_date=day,
        created_by=current_user.id,
        assigned_to=current_user.id,
    )
    db.session.add(task)
    db.session.commit()
    flash("Tâche créée — précisez-la si besoin.", "success")
    return redirect(url_for("tasks.edit", task_id=task.id))


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
