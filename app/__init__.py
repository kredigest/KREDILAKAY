# app/_init_.py

from flask import Flask

def create_app():
    app = Flask(__name__)
    # ... tes routes, configs, etc.
    return app
