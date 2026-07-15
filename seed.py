"""
Put the three customers api.py used to hardcode into MongoDB.

Wipes the collection first, so running it again resets you to a clean state.

    python seed.py
"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27018")
customers = client.banking.customers

CUSTOMERS = [
    {"name": "John Doe", "email": "john.doe@example.com", "balance": 5000.00},
    {"name": "Jane Smith", "email": "jane.smith@example.com", "balance": 7500.50},
    {"name": "Bob Johnson", "email": "bob.johnson@example.com", "balance": 3200.75},
]

if __name__ == "__main__":
    customers.delete_many({})
    customers.insert_many(CUSTOMERS)
    print(f"{customers.count_documents({})} customers in the database")
