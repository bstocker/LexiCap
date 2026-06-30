"""Sauvegarde et export : archive ZIP (base + documents) et bilan imprimable."""
import io
import os
import zipfile
from datetime import date

from flask import (
    Blueprint, abort, current_app, render_template, send_file,
)
from flask_login import current_user, login_required

from ..models import (
    Course, Document, Evaluation, Task, TdSession, WeeklyReview, Worksheet,
)

bp = Blueprint("exports", __name__, url_prefix="/exports")


@bp.route("/")
@login_required
def index():
    return render_template("exports/index.html")


@bp.route("/data.zip")
@login_required
def data_zip():
    # L'archive complète contient toutes les données : réservée à l'administrateur.
    if not current_user.is_admin:
        abort(403)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Base SQLite (si c'est bien le moteur utilisé).
        uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if uri.startswith("sqlite:///"):
            db_path = uri.replace("sqlite:///", "", 1)
            if os.path.exists(db_path):
                zf.write(db_path, arcname="lexicap.sqlite")

        # Documents uploadés.
        upload_dir = current_app.config["UPLOAD_FOLDER"]
        if os.path.isdir(upload_dir):
            for name in os.listdir(upload_dir):
                fpath = os.path.join(upload_dir, name)
                if os.path.isfile(fpath):
                    zf.write(fpath, arcname=f"uploads/{name}")

    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"lexicap-sauvegarde-{date.today().isoformat()}.zip",
    )


@bp.route("/print")
@login_required
def print_report():
    """Bilan synthétique imprimable (Imprimer → Enregistrer en PDF)."""
    tasks = Task.query.all()
    data = {
        "today": date.today(),
        "tasks_total": len(tasks),
        "tasks_done": sum(1 for t in tasks if t.is_done),
        "tasks_overdue": sum(1 for t in tasks if t.is_overdue),
        "courses_total": Course.query.count(),
        "courses_reviewed": Course.query.filter_by(reviewed=True).count(),
        "td_total": TdSession.query.count(),
        "ws_total": Worksheet.query.count(),
        "ws_validated": Worksheet.query.filter_by(status="Validée").count(),
        "documents": Document.query.count(),
        "evaluations": Evaluation.query.order_by(Evaluation.evaluation_date.desc()).all(),
        "last_review": WeeklyReview.query.order_by(WeeklyReview.week_date.desc()).first(),
    }
    return render_template("exports/print.html", **data)
