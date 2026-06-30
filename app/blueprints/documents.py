"""Documents et liens : dépôt de fichiers (PDF, Word…) et d'URL."""
import os
import secrets

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template,
    request, send_from_directory, url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from ..extensions import db
from ..forms import DocumentForm
from ..models import Document, Subject

bp = Blueprint("documents", __name__, url_prefix="/documents")


def _subject_choices():
    choices = [(0, "—")]
    choices += [(s.id, s.name) for s in Subject.query.filter_by(active=True).order_by(Subject.name)]
    return choices


def _save_file(file_storage):
    """Enregistre le fichier sur disque avec un nom unique. Renvoie (stored, original, size)."""
    original = secure_filename(file_storage.filename)
    stored = f"{secrets.token_hex(8)}_{original}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored)
    file_storage.save(path)
    size = os.path.getsize(path)
    return stored, original, size


@bp.route("/")
@login_required
def index():
    doc_type = request.args.get("type")
    query = Document.query
    if doc_type:
        query = query.filter_by(doc_type=doc_type)
    documents = query.order_by(Document.uploaded_at.desc()).all()
    return render_template("documents/list.html", documents=documents, current_type=doc_type)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = DocumentForm()
    form.subject_id.choices = _subject_choices()
    if form.validate_on_submit():
        doc = Document(
            title=form.title.data,
            doc_type=form.doc_type.data,
            subject_id=form.subject_id.data or None,
            tags=form.tags.data,
            uploaded_by=current_user.id,
        )
        if form.file.data:
            stored, original, size = _save_file(form.file.data)
            doc.filename = stored
            doc.original_name = original
            doc.size_bytes = size
        elif form.url.data:
            doc.url = form.url.data
        db.session.add(doc)
        db.session.commit()
        flash("Document ajouté.", "success")
        return redirect(url_for("documents.index"))
    return render_template("documents/form.html", form=form, title="Nouveau document")


@bp.route("/<int:doc_id>/download")
@login_required
def download(doc_id):
    doc = db.get_or_404(Document, doc_id)
    if not doc.filename:
        abort(404)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        doc.filename,
        as_attachment=True,
        download_name=doc.original_name or doc.filename,
    )


@bp.route("/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete(doc_id):
    doc = db.get_or_404(Document, doc_id)
    # Supprime aussi le fichier sur disque, le cas échéant.
    if doc.filename:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.filename)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(doc)
    db.session.commit()
    flash("Document supprimé.", "info")
    return redirect(url_for("documents.index"))
