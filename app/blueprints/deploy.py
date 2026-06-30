"""Webhook de déploiement.

Permet à une GitHub Action (ou un appel manuel) de déclencher la mise à jour du
code sur PythonAnywhere : l'application fait elle-même un `git pull` de son
dépôt. Le rechargement de la web app est effectué séparément par l'Action via
l'API de reload de PythonAnywhere (ce qui évite que la requête se coupe
elle-même en rechargeant le worker).

Sécurité :
- la route est désactivée tant qu'aucun jeton DEPLOY_TOKEN n'est configuré ;
- le jeton est comparé en temps constant (hmac.compare_digest) ;
- seule l'opération `git pull --ff-only` est exécutée (pas de commande arbitraire).
"""
import hmac
import subprocess
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("deploy", __name__)

# Racine du projet (le dossier qui contient le dépôt git) : app/blueprints/deploy.py -> ../../
PROJECT_DIR = Path(__file__).resolve().parents[2]


@bp.route("/deploy", methods=["POST"])
def deploy():
    token = current_app.config.get("DEPLOY_TOKEN")
    if not token:
        return jsonify(error="Déploiement non configuré (DEPLOY_TOKEN absent)."), 404

    provided = request.headers.get("X-Deploy-Token", "")
    if not hmac.compare_digest(provided, token):
        return jsonify(error="Jeton de déploiement invalide."), 403

    try:
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=f"Échec de l'exécution de git pull : {exc}"), 500

    if result.returncode != 0:
        return jsonify(
            error="git pull a échoué.",
            details=(result.stderr or result.stdout)[-800:],
        ), 500

    return jsonify(status="ok", output=result.stdout.strip()[-800:])
