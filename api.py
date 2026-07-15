"""
REST API for Banking System - Customers endpoint

Customer data now comes from MongoDB instead of a hardcoded list.
Start the database first:  docker compose up -d
Then put the customers in: python seed.py
"""

from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Port 27018, not Mongo's usual 27017: this machine already runs another MongoDB
# on 27017 (the crm-mongodb container). See docker-compose.yml.
client = MongoClient("mongodb://localhost:27018")
customers = client.banking.customers


def to_json(customer):
    """
    Turn a Mongo document into what the API hands out.

    Mongo's _id is an ObjectId, which jsonify can't serialise - hence str().
    It's renamed to plain `id` because the underscore is a Mongo detail.
    """
    return {
        "id": str(customer["_id"]),
        "name": customer["name"],
        "email": customer["email"],
        "balance": customer["balance"],
    }


@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get all customers"""
    return jsonify([to_json(c) for c in customers.find()])


@app.route('/api/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get one customer by id"""
    try:
        oid = ObjectId(customer_id)
    except InvalidId:
        # Not a real id, e.g. /api/customers/banana. The caller's mistake,
        # so 400 - without this it would be an unhelpful 500.
        return jsonify(error=f"'{customer_id}' is not a valid customer id"), 400

    customer = customers.find_one({"_id": oid})
    if customer is None:
        return jsonify(error=f"No customer with id {customer_id}"), 404
    return jsonify(to_json(customer))


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
