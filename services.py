"""
Service layer - the business rules.

The heart of the application, and the layer that knows the least about its
surroundings. It has no idea MongoDB exists (that's the repository's problem) and
no idea HTTP exists (that's the controller's). It only knows what a customer is
allowed to be.

That ignorance is the point. These rules run for EVERY caller - the web API,
seed.py, a script, you in a REPL - because there is no way to reach the
repository without coming through here. Put a rule in a route instead and it only
fires when that route is hit.

This is the same job the MODEL section of banking_system.py does on the `main`
branch: reject bad data before it can exist.
"""

import re

from exceptions import CustomerNotFound, ValidationError
from models import Customer
from repositories import CustomerRepository

# The same rule as banking_system.py:195, copied deliberately so both branches
# agree on what an email is: some text, an @, some text, a dot, some text, and no
# spaces anywhere. Rejects gibberish like "asdf" or "a b@c".
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CustomerService:
    """Business rules for customers."""

    def __init__(self, repository=None):
        """The repository is injectable, defaulting to the real one."""
        self._repository = repository or CustomerRepository()

    # Reads

    def list_customers(self):
        """Every customer."""
        return self._repository.find_all()

    def get_customer(self, customer_id):
        """
        One customer.

        Raises CustomerNotFound rather than returning None. That's a deliberate
        service-layer decision: "this customer doesn't exist" is an exceptional
        outcome the caller must handle, and raising means the controller can't
        forget to check - where a None would quietly become an AttributeError.
        """
        customer = self._repository.find_by_id(customer_id)
        if customer is None:
            raise CustomerNotFound(f"No customer with id {customer_id}")
        return customer

    # Writes

    def create_customer(self, data):
        """Validate and store a new customer."""
        customer = self._build(data, balance_required=False)
        return self._repository.insert(customer)

    def replace_customer(self, customer_id, data):
        """
        Replace a customer wholesale.

        Every field is required - see _build. The customer must already exist,
        so a missing id raises CustomerNotFound rather than creating one.
        """
        customer = self._build(data, balance_required=True)
        replaced = self._repository.replace(customer_id, customer)
        if replaced is None:
            raise CustomerNotFound(f"No customer with id {customer_id}")
        return replaced

    def delete_customer(self, customer_id):
        """Delete a customer, or raise if there's nothing to delete."""
        if not self._repository.delete(customer_id):
            raise CustomerNotFound(f"No customer with id {customer_id}")

    # Validation

    def _build(self, data, *, balance_required):
        """
        Validate a request body and turn it into a Customer.

        Mongo enforces no schema - it will happily store {"nmae": 42} forever and
        never complain. There is no CREATE TABLE and no migration to catch this.
        So this method is the only thing standing between a typo and the data.

        balance_required is what separates the two write operations:
          - create (POST): balance is optional, defaults to 0
          - replace (PUT): every field must be supplied

        That distinction matters more than it looks. PUT means "make the resource
        look exactly like this", so omitting balance must be a loud error - if it
        silently defaulted to 0, a partial update would wipe someone's money.
        """
        if not isinstance(data, dict):
            raise ValidationError("Body must be a JSON object")

        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name is required and must be a non-empty string")

        email = data.get("email")
        if not isinstance(email, str) or not EMAIL_PATTERN.match(email.strip()):
            raise ValidationError(
                "email is required and must look like name@example.com"
            )

        if "balance" in data:
            balance = data["balance"]
            # bool is a subclass of int in Python, so isinstance(True, int) is
            # True. Without this guard {"balance": true} would sail straight
            # through and store a balance of 1.
            if isinstance(balance, bool) or not isinstance(balance, (int, float)):
                raise ValidationError("balance must be a number")
            if balance < 0:
                raise ValidationError("balance cannot be negative")
            balance = float(balance)
        elif balance_required:
            raise ValidationError("balance is required")
        else:
            balance = 0.0

        return Customer(
            name=name.strip(),
            # Lowercased so the unique index actually means something - otherwise
            # Bob@x.com and bob@x.com would be accepted as two different people.
            email=email.strip().lower(),
            balance=balance,
        )
