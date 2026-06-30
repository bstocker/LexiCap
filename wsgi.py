"""Point d'entrée WSGI pour la production (Gunicorn, PythonAnywhere).

Sur PythonAnywhere, le fichier WSGI de la webapp peut simplement faire :

    import sys
    path = "/home/<USER>/LexiCap"
    if path not in sys.path:
        sys.path.insert(0, path)
    from wsgi import app as application
"""
from app import create_app

app = create_app()
application = app  # alias attendu par certains serveurs WSGI
