"""Modèles de données LexiCap.

Toutes les tables du MVP sont regroupées ici pour garder le projet simple et
lisible. Les libellés (statuts, types, priorités) sont définis comme listes de
constantes réutilisées par les formulaires et les gabarits.
"""
from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager

# ---------------------------------------------------------------------------
# Listes de valeurs (réutilisées dans les formulaires)
# ---------------------------------------------------------------------------
ROLES = ["student", "parent", "tutor", "admin"]
ROLE_LABELS = {
    "student": "Étudiante",
    "parent": "Parent",
    "tutor": "Tuteur",
    "admin": "Administrateur",
}

SEMESTERS = ["S1", "S2"]
COURSE_TYPES = ["CM", "TD", "CM+TD"]
PERCEIVED_LEVELS = ["Facile", "Moyen", "Difficile"]

TASK_TYPES = [
    "Relecture", "Fiche", "TD", "Révision",
    "Méthode", "Tutorat", "Administratif", "Exercice",
]
PRIORITIES = ["Basse", "Moyenne", "Haute"]
TASK_STATUSES = ["À faire", "En cours", "Bloquée", "Terminée", "Reportée", "Annulée"]

COURSE_STATUSES = ["À relire", "Relu", "Fiche à faire", "Fiche faite", "À revoir"]

TD_METHODS = ["Dissertation", "Cas pratique", "Commentaire d'arrêt"]
TD_STATUSES = ["Non commencé", "Documents lus", "Brouillon fait", "Prêt", "Corrigé repris"]

WORKSHEET_STATUSES = ["À faire", "Brouillon", "À relire", "Validée", "À revoir", "Archivée"]

QUESTION_TYPES = ["Compréhension", "Méthode", "Correction", "Révision", "Partiel", "Organisation"]
QUESTION_STATUSES = ["À poser", "Posée", "Réponse à revoir", "Transformée en tâche", "Clôturée"]
QUESTION_SOURCES = ["Cours", "Fiche", "TD", "Tâche", "Autre"]

EVAL_TYPES = [
    "Devoir maison", "TD noté", "Interrogation",
    "Galop d'essai", "Partiel", "Oral", "Examen blanc",
]
EVAL_STATUSES = ["À préparer", "En révision", "Passée", "Corrigée", "Exploitée"]

DOC_TYPES = [
    "Cours", "Fiche", "TD", "Correction", "Annale",
    "Méthodologie", "Administratif", "Autre",
]

WEEKDAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
SLOT_TYPES = ["CM", "TD", "Révision", "Travail perso", "Autre"]
# Couleur de fond par type de créneau (cohérente avec le reste de l'app).
SLOT_COLORS = {
    "CM": "#1e3a8a",
    "TD": "#0d9488",
    "Révision": "#16a34a",
    "Travail perso": "#6b7280",
    "Autre": "#9ca3af",
}


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------------
# Utilisateurs
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    role = db.Column(db.String(20), nullable=False, default="student")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login : un compte désactivé ne peut pas se connecter.
    @property
    def is_active(self):
        return self.active

    @property
    def full_name(self):
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return name or self.email

    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_tutor(self):
        return self.role == "tutor"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# ---------------------------------------------------------------------------
# Matières
# ---------------------------------------------------------------------------
class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    semester = db.Column(db.String(10), default="S1")
    type = db.Column(db.String(20))
    coefficient = db.Column(db.Float)
    teacher_name = db.Column(db.String(120))
    td_teacher_name = db.Column(db.String(120))
    perceived_level = db.Column(db.String(20))
    color = db.Column(db.String(20), default="#2563eb")
    active = db.Column(db.Boolean, nullable=False, default=True)

    courses = db.relationship("Course", backref="subject", cascade="all, delete-orphan")
    tasks = db.relationship("Task", backref="subject")
    worksheets = db.relationship("Worksheet", backref="subject", cascade="all, delete-orphan")
    td_sessions = db.relationship("TdSession", backref="subject", cascade="all, delete-orphan")
    evaluations = db.relationship("Evaluation", backref="subject", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject {self.name}>"


# ---------------------------------------------------------------------------
# Cours
# ---------------------------------------------------------------------------
class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    course_date = db.Column(db.Date, nullable=False, default=date.today)
    course_type = db.Column(db.String(20), default="CM")
    support_available = db.Column(db.Boolean, default=False)
    reviewed = db.Column(db.Boolean, default=False)
    review_date = db.Column(db.Date)
    worksheet_created = db.Column(db.Boolean, default=False)
    comprehension_level = db.Column(db.Integer)  # 1 à 5
    notes = db.Column(db.Text)

    @property
    def status(self):
        if self.comprehension_level and self.comprehension_level <= 2:
            return "À revoir"
        if self.worksheet_created:
            return "Fiche faite"
        if self.reviewed:
            return "Fiche à faire"
        return "À relire"

    @property
    def is_overdue_review(self):
        """RG-001 : cours non relu plus de 48h après la séance."""
        if self.reviewed:
            return False
        return (date.today() - self.course_date).days >= 2


# ---------------------------------------------------------------------------
# Tâches
# ---------------------------------------------------------------------------
class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"))
    task_type = db.Column(db.String(30), default="Relecture")
    priority = db.Column(db.String(20), default="Moyenne")
    status = db.Column(db.String(20), default="À faire")
    due_date = db.Column(db.Date)
    estimated_minutes = db.Column(db.Integer)
    actual_minutes = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    creator = db.relationship("User", foreign_keys=[created_by])
    assignee = db.relationship("User", foreign_keys=[assigned_to])

    DONE_STATUSES = ("Terminée", "Annulée")

    @property
    def is_done(self):
        return self.status in self.DONE_STATUSES

    @property
    def is_overdue(self):
        if self.is_done or not self.due_date:
            return False
        return self.due_date < date.today()


# ---------------------------------------------------------------------------
# TD (travaux dirigés)
# ---------------------------------------------------------------------------
class TdSession(db.Model):
    __tablename__ = "td_sessions"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    td_date = db.Column(db.Date, nullable=False, default=date.today)
    theme = db.Column(db.String(200), nullable=False)
    documents = db.Column(db.Text)
    exercise = db.Column(db.Text)
    method = db.Column(db.String(40))
    status = db.Column(db.String(30), default="Non commencé")
    correction_reviewed = db.Column(db.Boolean, default=False)

    @property
    def is_ready(self):
        return self.status in ("Prêt", "Corrigé repris")

    @property
    def days_left(self):
        return (self.td_date - date.today()).days

    @property
    def is_urgent(self):
        """RG-002 : TD non prêt à moins de 3 jours."""
        if self.is_ready:
            return False
        return 0 <= self.days_left <= 3


# ---------------------------------------------------------------------------
# Fiches de révision
# ---------------------------------------------------------------------------
class Worksheet(db.Model):
    __tablename__ = "worksheets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    chapter = db.Column(db.String(120))
    content_md = db.Column(db.Text)
    status = db.Column(db.String(20), default="Brouillon")
    mastery_level = db.Column(db.Integer)  # 1 à 5
    last_review_date = db.Column(db.Date)
    next_review_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship("Course", backref="worksheets")

    @property
    def needs_review(self):
        """RG-004 + répétition espacée : fiche fragile ou échéance atteinte."""
        if self.mastery_level and self.mastery_level <= 2:
            return True
        if self.next_review_date and self.next_review_date <= date.today():
            return True
        return False


# ---------------------------------------------------------------------------
# Questions pour le tuteur
# ---------------------------------------------------------------------------
class TutorialQuestion(db.Model):
    __tablename__ = "tutorial_questions"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"))
    source_type = db.Column(db.String(20))
    source_id = db.Column(db.Integer)
    question_type = db.Column(db.String(30), default="Compréhension")
    priority = db.Column(db.String(20), default="Moyenne")
    status = db.Column(db.String(30), default="À poser")
    tutor_answer = db.Column(db.Text)
    action_text = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)

    subject = db.relationship("Subject")

    OPEN_STATUSES = ("À poser", "Posée", "Réponse à revoir")

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES


# ---------------------------------------------------------------------------
# Séances de tutorat
# ---------------------------------------------------------------------------
class TutoringSession(db.Model):
    __tablename__ = "tutoring_sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.Date, nullable=False, default=date.today)
    duration_minutes = db.Column(db.Integer)
    tutor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    summary = db.Column(db.Text)
    understood_points = db.Column(db.Text)
    fragile_points = db.Column(db.Text)
    next_actions = db.Column(db.Text)

    tutor = db.relationship("User")


# ---------------------------------------------------------------------------
# Évaluations
# ---------------------------------------------------------------------------
class Evaluation(db.Model):
    __tablename__ = "evaluations"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    evaluation_type = db.Column(db.String(30), default="Galop d'essai")
    evaluation_date = db.Column(db.Date, nullable=False, default=date.today)
    coefficient = db.Column(db.Float)
    method = db.Column(db.String(40))
    subject_text = db.Column(db.Text)
    grade = db.Column(db.Float)
    correction_comment = db.Column(db.Text)
    improvement_action = db.Column(db.String(255))
    status = db.Column(db.String(20), default="À préparer")

    @property
    def days_left(self):
        return (self.evaluation_date - date.today()).days

    @property
    def is_upcoming(self):
        """RG-005 : évaluation à moins de 10 jours."""
        return 0 <= self.days_left <= 10


# ---------------------------------------------------------------------------
# Bilan hebdomadaire
# ---------------------------------------------------------------------------
class WeeklyReview(db.Model):
    __tablename__ = "weekly_reviews"

    id = db.Column(db.Integer, primary_key=True)
    week_date = db.Column(db.Date, nullable=False, default=date.today)
    summary = db.Column(db.Text)
    done = db.Column(db.Text)
    not_done = db.Column(db.Text)
    blockers = db.Column(db.Text)
    perceived_load = db.Column(db.Integer)  # 1 à 5
    confidence = db.Column(db.Integer)      # 1 à 5
    fatigue = db.Column(db.Integer)         # 1 à 5
    next_priorities = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Suivi de l'activité (connexions) — nouvelle table, n'altère rien d'existant
# ---------------------------------------------------------------------------
class LoginEvent(db.Model):
    __tablename__ = "login_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User")


# ---------------------------------------------------------------------------
# Documents et liens
# ---------------------------------------------------------------------------
class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    doc_type = db.Column(db.String(30), default="Autre")
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"))
    # Un document est soit un fichier (filename/original_name), soit un lien (url).
    url = db.Column(db.String(500))
    filename = db.Column(db.String(255))       # nom stocké sur le disque
    original_name = db.Column(db.String(255))  # nom d'origine, pour le téléchargement
    size_bytes = db.Column(db.Integer)
    tags = db.Column(db.String(255))
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship("Subject")
    uploader = db.relationship("User")

    @property
    def is_link(self):
        return bool(self.url)

    @property
    def is_file(self):
        return bool(self.filename)

    @property
    def size_kb(self):
        return round((self.size_bytes or 0) / 1024, 1)


# ---------------------------------------------------------------------------
# Emploi du temps : créneaux hebdomadaires récurrents
# ---------------------------------------------------------------------------
class ScheduleSlot(db.Model):
    __tablename__ = "schedule_slots"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"))
    day_of_week = db.Column(db.Integer, nullable=False)  # 0 = Lundi … 5 = Samedi
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_type = db.Column(db.String(20), default="CM")
    room = db.Column(db.String(80))
    note = db.Column(db.String(200))

    subject = db.relationship("Subject")

    @property
    def start_minutes(self):
        return self.start_time.hour * 60 + self.start_time.minute

    @property
    def end_minutes(self):
        return self.end_time.hour * 60 + self.end_time.minute

    @property
    def color(self):
        return SLOT_COLORS.get(self.slot_type, "#9ca3af")

    @property
    def day_name(self):
        if 0 <= self.day_of_week < len(WEEKDAYS):
            return WEEKDAYS[self.day_of_week]
        return "?"


# ---------------------------------------------------------------------------
# Préférences applicatives (table clé/valeur réutilisable)
# ---------------------------------------------------------------------------
class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(60), primary_key=True)
    value = db.Column(db.String(255))


def get_setting(key, default=None):
    s = db.session.get(Setting, key)
    return s.value if s is not None else default


def set_setting(key, value):
    s = db.session.get(Setting, key)
    if s is None:
        db.session.add(Setting(key=key, value=str(value)))
    else:
        s.value = str(value)
    db.session.commit()
