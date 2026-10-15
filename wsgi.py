"""Point d'entrée : `gunicorn wsgi:app` en production, `python wsgi.py` en local."""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5055)), debug=os.environ.get("FLASK_DEBUG") == "1")
