from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.from_pyfile('../config.py')  # Ajustez selon la localisation réelle de config.py
    
    # Extensions
    db.init_app(app)
    CORS(app)

    # Enregistrement des blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.loan_routes import loan_bp
    from app.routes.admin_routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(loan_bp, url_prefix='/loans')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
