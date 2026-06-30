#!/usr/bin/env bash
#
# Déploiement de LexiCap sur PythonAnywhere.
#
# À lancer depuis une console Bash PythonAnywhere :
#     bash ~/mysite/deploy.sh
#
# Le script récupère la dernière version du code depuis GitHub, installe les
# éventuelles nouvelles dépendances, puis recharge la web app (en « touchant »
# le fichier WSGI, ce qui déclenche un reload sans avoir besoin de l'interface).
#
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Récupération du code depuis GitHub..."
git pull --ff-only

echo "==> Installation des dépendances (si nouvelles)..."
python3.13 -m pip install --user -r requirements.txt

echo "==> Rechargement de la web app..."
# Touch du fichier WSGI de la web app : déclenche un reload immédiat.
touch /var/www/*_wsgi.py 2>/dev/null || echo "   (fichier WSGI introuvable — rechargez via l'onglet Web)"

echo "==> Terminé. Rafraîchissez votre site dans le navigateur."
