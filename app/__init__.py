from flask import Flask
from .database import db
from config.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        from .auth import login, signup
        from .chrome import routes as chrome_routes

        db.create_all()  # Crea las tablas en la base de datos

        # Registro de Blueprints (seguridad y Chrome)
        app.register_blueprint(login.bp)
        app.register_blueprint(signup.bp)
        app.register_blueprint(chrome_routes.bp)

    return app