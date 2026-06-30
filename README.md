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

## Déploiement (PythonAnywhere, par git)

Le déploiement se fait par **git pull** sur PythonAnywhere — fiable pour le code
comme pour les fichiers binaires (logo, favicon).

> L'ancien workflow GitHub Actions (`.github/workflows/CICD.yml`, upload via
> l'API Files) est **déprécié** : il déposait des fichiers vides et corrompait
> les binaires. Il est conservé en déclenchement manuel uniquement.

**Première installation** (une seule fois, dans une console Bash PythonAnywhere) :

```bash
cd ~/mysite
git init -q
git remote add origin https://github.com/bstocker/LexiCap.git
git fetch origin main
git reset --hard origin/main
python3.13 -m pip install --user -r requirements.txt
```

Puis, onglet **Web** de PythonAnywhere :
- *WSGI configuration file* → la ligne d'import doit être `from wsgi import app as application` ;
- cliquer sur **Reload**.

Aucune commande `flask init-db` n'est nécessaire : les tables et la clé secrète
sont créées automatiquement au premier chargement, et le premier compte
administrateur se crée via l'assistant web (`/setup`).

### Mises à jour automatiques via GitHub Actions (recommandé)

Une fois l'app en place, on peut déployer automatiquement à chaque `git push`
(ou via le bouton **Run workflow** de l'onglet Actions). Le workflow appelle le
webhook `/deploy` de l'app (qui fait un `git pull` côté PythonAnywhere) puis
recharge la web app.

Configuration unique :

1. Générer un jeton : `python -c "import secrets; print(secrets.token_hex(32))"`.
2. Sur PythonAnywhere, l'ajouter dans `~/mysite/.env` : `DEPLOY_TOKEN=<le-jeton>`
   (créer le fichier `.env` s'il n'existe pas), puis **Reload** la web app.
3. Dans GitHub : *Settings > Secrets and variables > Actions*, ajouter le secret
   `DEPLOY_TOKEN` (même valeur), et vérifier que `PA_WEBAPP_DOMAIN`, `PA_USERNAME`,
   `PA_TOKEN` sont présents.

Sur un compte PythonAnywhere **gratuit**, si le `git pull` du webhook échoue avec
une erreur réseau, ajouter dans `~/mysite/.env` :
`HTTPS_PROXY=http://proxy.server:3128`.

### Mise à jour manuelle (alternative)

Depuis une console Bash PythonAnywhere :

```bash
bash ~/mysite/deploy.sh
```

(le script fait `git pull`, installe les nouvelles dépendances et recharge la web app)

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
