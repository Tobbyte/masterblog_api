"""Module to set up Swagger UI for the Masterblog API."""

from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = "/api/docs"
API_URL = "/static/swagger_masterblog.json"


def init_swagger_ui(app: Flask) -> None:
    """Initialize Swagger UI for the Flask app."""
    swagger_ui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            "app_name": "Masterblog_api",
        },
    )
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
