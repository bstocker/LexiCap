"""Bilans hebdomadaires."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from ..extensions import db
from ..forms import WeeklyReviewForm
from ..models import WeeklyReview

bp = Blueprint("reviews", __name__, url_prefix="/reviews")


def _apply_form(review, form):
    review.week_date = form.week_date.data
    review.done = form.done.data
    review.not_done = form.not_done.data
    review.blockers = form.blockers.data
    review.next_priorities = form.next_priorities.data
    review.perceived_load = int(form.perceived_load.data) if form.perceived_load.data else None
    review.confidence = int(form.confidence.data) if form.confidence.data else None
    review.fatigue = int(form.fatigue.data) if form.fatigue.data else None


@bp.route("/")
@login_required
def index():
    reviews = WeeklyReview.query.order_by(WeeklyReview.week_date.desc()).all()
    return render_template("reviews/list.html", reviews=reviews)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = WeeklyReviewForm()
    if form.validate_on_submit():
        review = WeeklyReview()
        _apply_form(review, form)
        db.session.add(review)
        db.session.commit()
        flash("Bilan enregistré.", "success")
        return redirect(url_for("reviews.detail", review_id=review.id))
    return render_template("reviews/form.html", form=form, title="Nouveau bilan")


@bp.route("/<int:review_id>")
@login_required
def detail(review_id):
    review = db.get_or_404(WeeklyReview, review_id)
    return render_template("reviews/detail.html", review=review)


@bp.route("/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
def edit(review_id):
    review = db.get_or_404(WeeklyReview, review_id)
    form = WeeklyReviewForm(obj=review)
    if form.validate_on_submit():
        _apply_form(review, form)
        db.session.commit()
        flash("Bilan mis à jour.", "success")
        return redirect(url_for("reviews.detail", review_id=review.id))
    # Pré-remplit les SelectField numériques en lecture.
    for field in ("perceived_load", "confidence", "fatigue"):
        value = getattr(review, field)
        if value is not None:
            getattr(form, field).data = str(value)
    return render_template("reviews/form.html", form=form, title="Modifier le bilan")
