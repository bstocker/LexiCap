"""Progressive Web App : manifeste et service worker servis à la racine.

Servir le service worker depuis « / » (et non /static/) lui donne une portée
sur tout le site, ce qui permet l'installation sur l'écran d'accueil mobile.
"""
from flask import Blueprint, Response, url_for

bp = Blueprint("pwa", __name__)


@bp.route("/manifest.webmanifest")
def manifest():
    data = {
        "name": "LexiCap — Suivi L1 Droit",
        "short_name": "LexiCap",
        "description": "Accompagnement méthodologique L1 Droit",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f6f7fb",
        "theme_color": "#1e3a8a",
        "lang": "fr",
        "icons": [
            {"src": url_for("static", filename="img/icon-192.png"),
             "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": url_for("static", filename="img/icon-512.png"),
             "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    from flask import jsonify
    resp = jsonify(data)
    resp.headers["Content-Type"] = "application/manifest+json"
    return resp


@bp.route("/sw.js")
def service_worker():
    # Service worker minimal : permet l'installation. On reste en "network-first"
    # simple (pas de mise en cache agressive, pour toujours servir la version à jour).
    js = """
const CACHE = 'lexicap-v1';
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
self.addEventListener('fetch', e => {
  // On laisse passer les requêtes normalement (réseau), avec repli cache hors-ligne.
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
"""
    return Response(js, mimetype="application/javascript")
