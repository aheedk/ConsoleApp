"""
Controller layer - HTTP, and only HTTP.

Each route does exactly three things: pull data out of the request, call one
service method, and choose a status code. There is no business logic here and no
`import pymongo` - if a route ever grows an `if`, that logic probably belongs in
the service.

A Blueprint rather than @app.route: a Blueprint is a group of routes that can be
registered onto an app later. That's what lets api.py own the app while this file
owns the routes, instead of every module reaching for the same global `app`.
url_prefix means the paths below are relative - '' is really '/api/customers'.
"""

from flask import Blueprint, jsonify, request

from exceptions import (
    CustomerNotFound,
    DatabaseUnavailable,
    DuplicateEmail,
    InvalidCustomerId,
    ValidationError,
)
from services import CustomerService

customers_blueprint = Blueprint("customers", __name__, url_prefix="/api/customers")

_service = CustomerService()


# This table is where HTTP meets the domain, and it lives here rather than on the
# exceptions themselves so that services.py stays free of web concepts.
#
# The three "your request failed" codes are genuinely different messages:
#   400 - you sent something malformed. Don't retry unchanged.
#   404 - well-formed, but that customer doesn't exist.
#   409 - well-formed and valid, but it conflicts with data that already exists.
#         Tells the caller to change the email and retry, where a 400 would
#         wrongly say their JSON was broken.
#   503 - this API is fine, its dependency isn't.
ERROR_STATUS = {
    ValidationError: 400,
    InvalidCustomerId: 400,
    CustomerNotFound: 404,
    DuplicateEmail: 409,
    DatabaseUnavailable: 503,
}


def _body():
    """
    The request's JSON body, or a clean 400.

    get_json() raises on a non-JSON body; get_json(silent=True) returns None
    instead. Same event either way, but one is a controlled response and the
    other is a stack trace.
    """
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError(
            "Body must be valid JSON, sent with Content-Type: application/json"
        )
    return data


@customers_blueprint.get('')
def get_customers():
    """GET /api/customers - all customers"""
    customers = _service.list_customers()
    return jsonify([c.to_dict() for c in customers])


@customers_blueprint.get('/<customer_id>')
def get_customer(customer_id):
    """GET /api/customers/<id> - one customer"""
    customer = _service.get_customer(customer_id)
    return jsonify(customer.to_dict())


@customers_blueprint.post('')
def create_customer():
    """POST /api/customers - create one. 201 + where to find it."""
    customer = _service.create_customer(_body())
    return (
        jsonify(customer.to_dict()),
        201,
        {"Location": f"/api/customers/{customer.id}"},
    )


@customers_blueprint.put('/<customer_id>')
def replace_customer(customer_id):
    """
    PUT /api/customers/<id> - replace one wholesale.

    name, email and balance are all required. Partial updates would be PATCH,
    which doesn't exist here.
    """
    customer = _service.replace_customer(customer_id, _body())
    return jsonify(customer.to_dict())


@customers_blueprint.delete('/<customer_id>')
def delete_customer(customer_id):
    """DELETE /api/customers/<id> - 204, done and deliberately nothing to say."""
    _service.delete_customer(customer_id)
    return "", 204
