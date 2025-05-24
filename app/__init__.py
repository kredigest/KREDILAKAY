from flask import Flask

def create_app():
    app = Flask(_name_)
    app.config['SECRET_KEY'] = 'your-secret'
    return app
