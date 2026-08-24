import os

from flask import Flask

from . import db


def create_app():
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = os.environ.get("DATABASE_PATH", "data/cafforize.db")

    db.init_app(app)

    from .routes import bp

    app.register_blueprint(bp)

    return app
