"""
REST API for Banking System - entry point.

This file wires the layers together and starts the server. It holds no routes and
no logic of its own - that's the point. Everything it does is assembly:

    HTTP -> controllers -> services -> repositories -> database -> MongoDB
              (this file registers the first one and starts Flask)

Start the database first:  docker compose up -d
Then put the customers in: python seed.py
Then run this:             python api.py
"""

from flask import Flask, jsonify

import database
from controllers import ERROR_STATUS, customers_blueprint
from exceptions import AppError
from repositories import CustomerRepository


def create_app():
    """
    Build the application.

    A factory rather than a module-level `app = Flask(__name__)` so that creating
    an app is an explicit act you could do more than once - with different
    settings, say - instead of a side effect of importing this file.
    """
    app = Flask(__name__)
    app.register_blueprint(customers_blueprint)
    _register_error_handlers(app)
    return app


def _register_error_handlers(app):
    """
    Turn domain exceptions into JSON responses.

    Every failure leaves as {"error": "..."} with a matching status code. This is
    registered app-wide, which is what lets the controllers simply raise and get
    on with it - no try/except in a single route.

    Flask's own 404 and 405 are HTML pages by default. An HTML body reaching a
    client that called response.json() surfaces as an unintelligible parse error
    rather than the clear message we meant to send, so they're overridden too.
    """

    @app.errorhandler(AppError)
    def on_app_error(exc):
        # isinstance rather than a dict lookup on type(exc), so a subclass of one
        # of our exceptions would still map correctly.
        status = next(
            (code for cls, code in ERROR_STATUS.items() if isinstance(exc, cls)),
            500,
        )
        return jsonify(error=str(exc)), status

    @app.errorhandler(404)
    def on_not_found(exc):
        return jsonify(error="Not found"), 404

    @app.errorhandler(405)
    def on_method_not_allowed(exc):
        return jsonify(error="Method not allowed for this URL"), 405


if __name__ == '__main__':
    # Fail fast and legibly if the database isn't up, rather than discovering it
    # five seconds into someone's first request. MongoClient is lazy, so without
    # this the app would start perfectly happily against a database that isn't
    # there.
    try:
        database.ping()
        CustomerRepository().ensure_indexes()
    except AppError as exc:
        raise SystemExit(f"\n{exc}\n\nStart it with:  docker compose up -d\n")

    create_app().run(host='localhost', port=8080, debug=True)
