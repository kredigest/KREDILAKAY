from flask import jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return jsonify({
            'code': e.code,
            'message': e.description
        }), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.error(f'Unexpected error: {str(e)}')
        return jsonify({
            'code': 500,
            'message': 'Erreur interne du serveur'
        }), 500
