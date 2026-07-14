"""
REST API for Banking System - Customers endpoint
"""

from flask import Flask, jsonify

app = Flask(__name__)

# Hardcoded customers
CUSTOMERS = [
    {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "balance": 5000.00
    },
    {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "balance": 7500.50
    },
    {
        "id": 3,
        "name": "Bob Johnson",
        "email": "bob.johnson@example.com",
        "balance": 3200.75
    }
]

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get all customers"""
    return jsonify(CUSTOMERS)

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
