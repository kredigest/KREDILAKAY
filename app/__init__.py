from flask import Flask
from .routes import init_app as init_routes

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.from_pyfile('config.py')
    
    # Initialisation des routes
    init_routes(app)
    
    return app
