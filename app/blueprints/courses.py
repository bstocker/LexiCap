"""Suivi des cours."""
from datetime import date

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from ..extensions import db
from ..forms import CourseForm
from ..models import Course, Subject, TutorialQuestion, Worksheet

bp = Blueprint("courses", __name__, url_prefix="/courses")


def _subject_choices():
    return [(s.id, s.name) for s in Subject.query.filter_by(active=True).order_by(Subject.name)]


def _apply_form(course, form):
    course.subject_id = form.subject_id.data
    course.title = form.title.data
    course.course_date = form.course_date.data
    course.course_type = form.course_type.data
    course.support_available = form.support_available.data
    course.reviewed = form.reviewed.data
    course.review_date = form.review_date.data
    course.worksheet_created = form.worksheet_created.data
    course.comprehension_level = int(form.comprehension_level.data) if form.comprehension_level.data else None
    course.notes = form.notes.data


@bp.route("/")
@login_required
def index():
    courses = Course.query.order_by(Course.course_date.desc()).all()
    return render_template("courses/list.html", courses=courses)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = CourseForm()
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        course = Course()
        _apply_form(course, form)
        db.session.add(course)
        db.session.commit()
        flash("Cours ajouté.", "success")
        return redirect(url_for("courses.detail", course_id=course.id))
    return render_template("courses/form.html", form=form, title="Nouveau cours")


@bp.route("/<int:course_id>")
@login_required
def detail(course_id):
    course = db.get_or_404(Course, course_id)
    return render_template("courses/detail.html", course=course)


@bp.route("/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def edit(course_id):
    course = db.get_or_404(Course, course_id)
    form = CourseForm(obj=course)
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        _apply_form(course, form)
        db.session.commit()
        flash("Cours mis à jour.", "success")
        return redirect(url_for("courses.detail", course_id=course.id))
    return render_template("courses/form.html", form=form, title="Modifier le cours")


@bp.route("/<int:course_id>/mark-reviewed", methods=["POST"])
@login_required
def mark_reviewed(course_id):
    course = db.get_or_404(Course, course_id)
    course.reviewed = True
    course.review_date = date.today()
    db.session.commit()
    flash("Cours marqué comme relu.", "success")
    return redirect(url_for("courses.detail", course_id=course.id))


@bp.route("/<int:course_id>/create-worksheet", methods=["POST"])
@login_required
def create_worksheet(course_id):
    course = db.get_or_404(Course, course_id)
    worksheet = Worksheet(
        title=course.title,
        subject_id=course.subject_id,
        course_id=course.id,
        status="Brouillon",
    )
    course.worksheet_created = True
    db.session.add(worksheet)
    db.session.commit()
    flash("Fiche créée à partir du cours.", "success")
    return redirect(url_for("worksheets.edit", worksheet_id=worksheet.id))


@bp.route("/<int:course_id>/create-question", methods=["POST"])
@login_required
def create_question(course_id):
    course = db.get_or_404(Course, course_id)
    question = TutorialQuestion(
        question=f"[À propos du cours : {course.title}] ",
        subject_id=course.subject_id,
        source_type="Cours",
        source_id=course.id,
    )
    db.session.add(question)
    db.session.commit()
    flash("Question pour le tuteur créée.", "success")
    return redirect(url_for("questions.edit", question_id=question.id))
