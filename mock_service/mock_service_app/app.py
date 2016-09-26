"""
    This module contains flask app startup.
    We register blueprints for different blueprints with this app.
"""

# App specific URLs
from mock_service.mock_service_app.v1_mock import mock_blueprint
from mock_service.mock_service_app import app

app.register_blueprint(mock_blueprint)
