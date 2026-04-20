import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from app.extensions import db


def create_app() -> Flask:
    load_dotenv(Path(__file__).parent.parent / ".flaskenv", override=True)

    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

    db_user = os.environ.get("POSTGRES_USER", "tavern")
    db_password = os.environ.get("POSTGRES_PASSWORD", "tavern")
    db_host = os.environ.get("POSTGRES_HOST", "db")
    db_port = os.environ.get("POSTGRES_PORT", "5432")
    db_name = os.environ.get("POSTGRES_DB", "tavern_board")
    default_uri = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", default_uri)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Deferred imports break potential circular-import cycles
    from app.controllers.quests import quests_bp
    app.register_blueprint(quests_bp)

    from app.cli import seed_categories
    app.cli.add_command(seed_categories)

    with app.app_context():
        db.create_all()

    return app


app = create_app()
