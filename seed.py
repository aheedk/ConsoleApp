"""
Put the three customers api.py used to hardcode into MongoDB.

Wipes the collection first, so running it again resets you to a clean state.

    python seed.py

Note this goes through CustomerService, exactly like the API does - so the seed
data is validated by the same rules as anything posted over HTTP. That's the
layering paying off: there is no back door into the database that skips the
business rules. Flask isn't imported here at all.
"""

import database
from exceptions import AppError
from repositories import CustomerRepository
from services import CustomerService

CUSTOMERS = [
    {"name": "John Doe", "email": "john.doe@example.com", "balance": 5000.00},
    {"name": "Jane Smith", "email": "jane.smith@example.com", "balance": 7500.50},
    {"name": "Bob Johnson", "email": "bob.johnson@example.com", "balance": 3200.75},
]


def seed():
    database.ping()

    repository = CustomerRepository()
    repository.ensure_indexes()

    # Wipe via the repository: emptying the collection is a persistence concern,
    # not a business rule, so there's no service method for it.
    removed = repository.delete_all()
    if removed:
        print(f"removed {removed} existing customer(s)")

    service = CustomerService(repository)
    for data in CUSTOMERS:
        customer = service.create_customer(data)
        print(f"  created  {customer.id}  {customer.name}")

    print(f"\n{len(CUSTOMERS)} customers in the database")


if __name__ == "__main__":
    try:
        seed()
    except AppError as exc:
        raise SystemExit(f"\n{exc}\n\nStart it with:  docker compose up -d\n")
