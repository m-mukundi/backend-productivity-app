import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _database_uri():
    uri = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")
    # Render (and some other hosts) hand out "postgres://", but SQLAlchemy
    # requires the "postgresql://" scheme.
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return uri


class Config:
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-RESTful only lets Flask's own registered error handlers (e.g.
    # Flask-JWT-Extended's unauthorized/invalid/expired token handlers) run
    # when exceptions propagate; otherwise it swallows them into a generic
    # 500. Without this, an unauthenticated request in production (where
    # DEBUG/TESTING are off) gets a 500 instead of the intended 401.
    PROPAGATE_EXCEPTIONS = True

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_TOKEN_LOCATION = ["headers"]

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-flask-secret-change-me")
