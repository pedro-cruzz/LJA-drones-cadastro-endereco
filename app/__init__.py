from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'chave-secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sgsv.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        # --- ESTA PARTE É CRÍTICA ---
        # É ela que diz ao Flask que o arquivo routes.py existe
        from app.routes import bp 
        app.register_blueprint(bp)
        # ---------------------------

        from app import models
        db.create_all()

    return app