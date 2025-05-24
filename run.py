#!/usr/bin/env python3
import os
import click
from flask import Flask
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Loan  # Importer vos modèles

app = create_app(os.getenv('FLASK_ENV') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Loan': Loan}

@click.group()
def cli():
    """KrediGest Management CLI"""
    pass

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind')
@click.option('--port', default=5000, help='Port to listen')
def run(host, port):
    """Run development server"""
    app.run(host=host, port=port, debug=True)

@cli.command()
def test():
    """Run unit tests"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@cli.command()
@click.option('--workers', default=4, help='Number of workers')
def gunicorn_run(workers):
    """Run production server with Gunicorn"""
    from gunicorn.app.base import Application
    
    class FlaskApplication(Application):
        def init(self, parser, opts, args):
            return {
                'bind': f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', 5000)}",
                'workers': workers,
                'worker_class': 'gevent',
                'timeout': 120
            }
        
        def load(self):
            return app
    
    FlaskApplication().run()

@cli.command()
def celery_worker():
    """Start Celery worker"""
    from app.celery_utils import make_celery
    celery = make_celery(app)
    celery.start(argv=['worker', '--loglevel=info'])

@cli.command()
def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        click.echo("Database initialized")

if __name__ == '__main__':
    cli()
