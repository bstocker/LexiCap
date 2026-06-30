# LexiCap

Application web d'accompagnement méthodologique pour une étudiante en **première
année de licence de droit**. LexiCap sert de tableau de bord de suivi, de
planificateur de travail, de carnet de progression et de support de coordination
entre l'étudiante, le parent accompagnateur et le tuteur.

> L'étudiante reste responsable de son travail · le parent aide à structurer et
> anticiper · le tuteur aide sur le droit et la méthode · LexiCap rend le suivi
> clair et non conflictuel.

La spécification fonctionnelle complète est dans
[`expression_fonctionnelle_app_flask_suivi_l1_droit.md`](expression_fonctionnelle_app_flask_suivi_l1_droit.md).

## Fonctionnalités (MVP)

- Tableau de bord hebdomadaire avec alertes automatiques (cours à relire, TD à
  préparer, fiches à revoir, questions tuteur, évaluations proches, retards) ;
- Gestion des **matières**, **cours**, **tâches**, **TD**, **fiches de révision** ;
- **Questions pour le tuteur** et **séances de tutorat** ;
- **Évaluations** et notes avec actions correctives ;
- **Bilans hebdomadaires** (charge, confiance, fatigue) ;
- Authentification, rôles (étudiante / parent / tuteur / admin) et administration
  des comptes.

## Stack technique

Python 3.11+ · Flask · SQLAlchemy · Flask-Migrate · Flask-Login · Flask-WTF ·
Jinja2 · Bootstrap 5 · SQLite (local) / PostgreSQL (production).

## Installation et lancement (local)

```bash
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt

# Configuration : copier le modèle et adapter SECRET_KEY
cp .env.example .env

# Initialiser la base de données
export FLASK_APP=wsgi.py           # Windows : set FLASK_APP=wsgi.py
flask init-db

# Créer le compte administrateur, puis celui de l'étudiante
flask create-user --role admin
flask create-user --role student

# (optionnel) Pré-remplir les matières types de L1 Droit
flask seed-subjects

# Lancer
python run.py
```

L'application est alors accessible sur http://127.0.0.1:5000.

## Commandes CLI utiles

| Commande | Rôle |
|---|---|
| `flask init-db` | Crée les tables de la base |
| `flask create-user --role <role>` | Crée un compte (student / parent / tutor / admin) |
| `flask seed-subjects` | Ajoute les matières types de L1 Droit |

## Migrations de base de données

Pour faire évoluer le schéma proprement (recommandé hors prototypage) :

```bash
flask db init        # une seule fois
flask db migrate -m "message"
flask db upgrade
```

## Déploiement

Le dépôt contient un workflow GitHub Actions
(`.github/workflows/CICD.yml`) qui déploie sur **PythonAnywhere** à chaque push
sur `main`. Il nécessite les secrets de dépôt : `PA_USERNAME`, `PA_TOKEN`,
`PA_TARGET_DIR`, `PA_WEBAPP_DOMAIN` (et `PA_HOST` si compte EU).

Sur PythonAnywhere, configurer le fichier WSGI de la webapp pour importer
`application` depuis `wsgi.py` (voir le commentaire en tête de `wsgi.py`), définir
`SECRET_KEY` dans les variables d'environnement et exécuter `flask init-db`.

## Structure du projet

```
app/
├── __init__.py        # factory create_app + commandes CLI
├── extensions.py      # db, login_manager, migrate
├── models.py          # tous les modèles SQLAlchemy
├── forms.py           # formulaires Flask-WTF
├── blueprints/        # un module par domaine fonctionnel
├── templates/         # gabarits Jinja2 (Bootstrap 5)
└── static/            # CSS et logo
config.py              # configuration (SQLite par défaut)
wsgi.py / run.py       # points d'entrée production / local
```
