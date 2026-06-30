"""Formulaires WTForms de LexiCap.

Flask-WTF fournit automatiquement la protection CSRF sur tous ces formulaires.
Les listes de choix proviennent des constantes définies dans models.py.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField, DateField, FloatField, IntegerField, PasswordField,
    SelectField, StringField, SubmitField, TextAreaField, TimeField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, NumberRange, Optional, URL,
)

# Extensions de fichiers autorisées pour les documents.
ALLOWED_DOC_EXTENSIONS = [
    "pdf", "doc", "docx", "odt", "ppt", "pptx", "xls", "xlsx",
    "txt", "md", "rtf", "png", "jpg", "jpeg", "gif", "webp",
]

from . import models as m


def _choices(values):
    """Transforme une liste de libellés en couples (valeur, libellé)."""
    return [(v, v) for v in values]


# ---------------------------------------------------------------------------
# Authentification / utilisateurs
# ---------------------------------------------------------------------------
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    remember = BooleanField("Se souvenir de moi")
    submit = SubmitField("Se connecter")


class ProfileForm(FlaskForm):
    first_name = StringField("Prénom", validators=[Optional(), Length(max=80)])
    last_name = StringField("Nom", validators=[Optional(), Length(max=80)])
    password = PasswordField(
        "Nouveau mot de passe", validators=[Optional(), Length(min=8)]
    )
    confirm = PasswordField(
        "Confirmer le mot de passe",
        validators=[Optional(), EqualTo("password", message="Les mots de passe diffèrent.")],
    )
    submit = SubmitField("Enregistrer")


class FirstAdminForm(FlaskForm):
    """Création du tout premier compte (administrateur) au premier lancement."""
    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("Prénom", validators=[Optional(), Length(max=80)])
    last_name = StringField("Nom", validators=[Optional(), Length(max=80)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField(
        "Confirmer le mot de passe",
        validators=[DataRequired(), EqualTo("password", message="Les mots de passe diffèrent.")],
    )
    submit = SubmitField("Créer le compte administrateur")


class UserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("Prénom", validators=[Optional(), Length(max=80)])
    last_name = StringField("Nom", validators=[Optional(), Length(max=80)])
    role = SelectField("Rôle", choices=[(r, m.ROLE_LABELS[r]) for r in m.ROLES])
    active = BooleanField("Compte actif", default=True)
    password = PasswordField("Mot de passe", validators=[Optional(), Length(min=8)])
    submit = SubmitField("Enregistrer")


# ---------------------------------------------------------------------------
# Matières
# ---------------------------------------------------------------------------
class SubjectForm(FlaskForm):
    name = StringField("Nom", validators=[DataRequired(), Length(max=120)])
    semester = SelectField("Semestre", choices=_choices(m.SEMESTERS))
    type = SelectField("Type", choices=[("", "—")] + _choices(m.COURSE_TYPES), validators=[Optional()])
    coefficient = FloatField("Coefficient", validators=[Optional(), NumberRange(min=0)])
    teacher_name = StringField("Enseignant", validators=[Optional(), Length(max=120)])
    td_teacher_name = StringField("Chargé de TD", validators=[Optional(), Length(max=120)])
    perceived_level = SelectField(
        "Niveau ressenti", choices=[("", "—")] + _choices(m.PERCEIVED_LEVELS), validators=[Optional()]
    )
    color = StringField("Couleur", default="#2563eb")
    active = BooleanField("Active", default=True)
    submit = SubmitField("Enregistrer")


# ---------------------------------------------------------------------------
# Cours
# ---------------------------------------------------------------------------
class CourseForm(FlaskForm):
    subject_id = SelectField("Matière", coerce=int, validators=[DataRequired()])
    title = StringField("Titre", validators=[DataRequired(), Length(max=200)])
    course_date = DateField("Date du cours", validators=[DataRequired()])
    course_type = SelectField("Type", choices=_choices(m.COURSE_TYPES))
    support_available = BooleanField("Support disponible")
    reviewed = BooleanField("Relu")
    review_date = DateField("Date de relecture", validators=[Optional()])
    worksheet_created = BooleanField("Fiche créée")
    comprehension_level = SelectField(
        "Niveau de compréhension (1-5)",
        choices=[("", "—")] + [(str(i), str(i)) for i in range(1, 6)],
        validators=[Optional()],
    )
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Enregistrer")


# ---------------------------------------------------------------------------
# Tâches
# ---------------------------------------------------------------------------
class TaskForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    subject_id = SelectField("Matière", coerce=int, validators=[Optional()])
    task_type = SelectField("Type", choices=_choices(m.TASK_TYPES))
    priority = SelectField("Priorité", choices=_choices(m.PRIORITIES))
    status = SelectField("Statut", choices=_choices(m.TASK_STATUSES))
    due_date = DateField("Date limite", validators=[Optional()])
    estimated_minutes = IntegerField("Durée estimée (min)", validators=[Optional(), NumberRange(min=0)])
    actual_minutes = IntegerField("Durée réalisée (min)", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Enregistrer")


# ---------------------------------------------------------------------------
# TD
# ---------------------------------------------------------------------------
class TdForm(FlaskForm):
    subject_id = SelectField("Matière", coerce=int, validators=[DataRequired()])
    td_date = DateField("Date du TD", validators=[DataRequired()])
    theme = StringField("Thème", validators=[DataRequired(), Length(max=200)])
    documents = TextAreaField("Documents à lire", validators=[Optional()])
    exercise = TextAreaField("Exercice demandé", validators=[Optional()])
    method = SelectField("Méthode", choices=[("", "—")] + _choices(m.TD_METHODS), validators=[Optional()])
    status = SelectField("Statut", choices=_choices(m.TD_STATUSES))
    correction_reviewed = BooleanField("Correction reprise")
    submit = SubmitField("Enregistrer")


# ---------------------------------------------------------------------------
# Fiches de révision
# ---------------------------------------------------------------------------
class WorksheetForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired(), Length(max=200)])
    subject_id = SelectField("Matière", coerce=int, validators=[DataRequired()])
    course_id = SelectField("Cours lié", coerce=int, validators=[Optional()])
    chapter = StringField("Chapitre", validators=[Optional(), Length(max=120)])
    content_md = TextAreaField("Contenu (Markdown)", validators=[Optional()])
    status = SelectField("Statut", choices=_choices(m.WORKSHEET_STATUSES))
    mastery_level = SelectField(
        "Niveau de maîtrise (1-5)",
        choices=[("", "—")] + [(str(i), str(i)) for i in range(1, 6)],
        validators=[Optional()],
    )
    last_review_date = DateField("Dernière révision", validators=[Optional()])
    next_review_date = DateField("Prochaine révision", validators=[Optional()])
    submit = SubmitField("Enregistrer")


# ---------------------------------------------------------------------------
# Questions tuteur
# ---------------------------------------------------------------------------
class QuestionForm(FlaskForm):
    question = TextAreaField("Question", validators=[DataRequired()])
    subject_id = SelectField("Matière", coerce=int, validators=[Optional()])
    question_type = SelectField("Type", choices=_choices(m.QUESTION_TYPES))
    priority = SelectField("Priorité", choices=_choices(m.PRIORITIES))
    status = SelectField("Statut", choices=_choices(m.QUESTION_STATUSES))
    submit = SubmitField("Enregistrer")


class AnswerForm(FlaskForm):
    tutor_answer = TextAreaField("Réponse du tuteur", validators=[DataRequired()])
    action_text = StringField("Action associée", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Enregistrer la réponse")


# ---------------------------------------------------------------------------
# Séances de tutorat
# ---------------------------------------------------------------------------
class TutoringForm(FlaskForm):
    session_date = DateField("Date", validators=[DataRequired()])
    duration_minutes = IntegerField("Durée (min)", validators=[Optional(), NumberRange(min=0)])
    summary = TextAreaField("Sujets traités", validators=[Optional()])
    understood_points = TextAreaField("Points compris", validators=[Optional()])
    fragile_points = TextAreaField("Points fragiles", validators=[Optional()])
    next_actions = TextAreaField("Actions à faire", validators=[Optional()])
    submit = SubmitField("Enregistrer")


# ---------------------------------------------------------------------------
# Évaluations
# ---------------------------------------------------------------------------
class EvaluationForm(FlaskForm):
    subject_id = SelectField("Matière", coerce=int, validators=[DataRequired()])
    evaluation_type = SelectField("Type", choices=_choices(m.EVAL_TYPES))
    evaluation_date = DateField("Date", validators=[DataRequired()])
    coefficient = FloatField("Coefficient", validators=[Optional(), NumberRange(min=0)])
    method = SelectField("Méthode", choices=[("", "—")] + _choices(m.TD_METHODS), validators=[Optional()])
    subject_text = TextAreaField("Sujet", validators=[Optional()])
    grade = FloatField("Note /20", validators=[Optional(), NumberRange(min=0, max=20)])
    correction_comment = TextAreaField("Commentaire de correction", validators=[Optional()])
    improvement_action = StringField("Action corrective", validators=[Optional(), Length(max=255)])
    status = SelectField("Statut", choices=_choices(m.EVAL_STATUSES))
    submit = SubmitField("Enregistrer")


# ---------------------------------------------------------------------------
# Documents et liens
# ---------------------------------------------------------------------------
class DocumentForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired(), Length(max=200)])
    doc_type = SelectField("Type", choices=_choices(m.DOC_TYPES))
    subject_id = SelectField("Matière", coerce=int, validators=[Optional()])
    file = FileField(
        "Fichier",
        validators=[
            Optional(),
            FileAllowed(ALLOWED_DOC_EXTENSIONS, "Type de fichier non autorisé."),
        ],
    )
    url = StringField("…ou lien (URL)", validators=[Optional(), URL(message="URL invalide."), Length(max=500)])
    tags = StringField("Tags (séparés par des virgules)", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Enregistrer")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        # Il faut au moins un fichier OU une URL (sauf en modification d'un doc existant).
        if not self.file.data and not self.url.data and not getattr(self, "_editing", False):
            msg = "Fournissez un fichier ou une URL."
            self.file.errors.append(msg)
            return False
        return True


# ---------------------------------------------------------------------------
# Emploi du temps
# ---------------------------------------------------------------------------
class ScheduleSlotForm(FlaskForm):
    day_of_week = SelectField(
        "Jour", coerce=int, choices=[(i, j) for i, j in enumerate(m.WEEKDAYS)]
    )
    start_time = TimeField(
        "Début", format=["%H:%M", "%H:%M:%S"], render_kw={"type": "time"}
    )
    end_time = TimeField(
        "Fin", format=["%H:%M", "%H:%M:%S"], render_kw={"type": "time"}
    )
    subject_id = SelectField("Matière", coerce=int, validators=[Optional()])
    slot_type = SelectField("Type", choices=_choices(m.SLOT_TYPES))
    room = StringField("Salle", validators=[Optional(), Length(max=80)])
    note = StringField("Note", validators=[Optional(), Length(max=200)])
    submit = SubmitField("Enregistrer")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        if self.start_time.data and self.end_time.data and self.end_time.data <= self.start_time.data:
            self.end_time.errors.append("L'heure de fin doit être après le début.")
            return False
        return True


# ---------------------------------------------------------------------------
# Bilan hebdomadaire
# ---------------------------------------------------------------------------
class WeeklyReviewForm(FlaskForm):
    week_date = DateField("Semaine du", validators=[DataRequired()])
    done = TextAreaField("Ce qui a été fait", validators=[Optional()])
    not_done = TextAreaField("Ce qui n'a pas été fait", validators=[Optional()])
    blockers = TextAreaField("Points de blocage", validators=[Optional()])
    next_priorities = TextAreaField("Priorités semaine prochaine", validators=[Optional()])
    perceived_load = SelectField(
        "Charge ressentie (1-5)", choices=[("", "—")] + [(str(i), str(i)) for i in range(1, 6)],
        validators=[Optional()],
    )
    confidence = SelectField(
        "Confiance (1-5)", choices=[("", "—")] + [(str(i), str(i)) for i in range(1, 6)],
        validators=[Optional()],
    )
    fatigue = SelectField(
        "Fatigue (1-5)", choices=[("", "—")] + [(str(i), str(i)) for i in range(1, 6)],
        validators=[Optional()],
    )
    submit = SubmitField("Enregistrer")
