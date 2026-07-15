"""
Repository layer - all the MongoDB queries, and nothing else.

This is the ONLY module that writes a query. It is the translation boundary
between Mongo and the rest of the app, and it translates in both directions:

    in   - Customer models and plain string ids
    out  - Customer models. Never a raw document, never an ObjectId.
    errors - pymongo/bson exceptions become domain exceptions from exceptions.py

Because of that, nothing above this layer imports pymongo or bson. If you ever
replaced MongoDB with Postgres, this file is the only one that would change.

There are no business rules here. This layer will happily store a customer with a
nonsense email - deciding what's allowed is the service's job. This one only
knows how to put things in and get them out.
"""

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError

import database
from exceptions import DatabaseUnavailable, DuplicateEmail, InvalidCustomerId
from models import Customer


class CustomerRepository:
    """Persistence for Customer."""

    def __init__(self, collection=None):
        """
        The collection is injectable, defaulting to the real one.

        That's not ceremony: it means this class can be pointed at a different
        collection without touching the code - a test database, say - and it's
        why the layering earns its keep.
        """
        self._collection = collection or database.get_collection("customers")

    # Helpers

    @staticmethod
    def _object_id(customer_id):
        """
        Turn a string id from a URL into the ObjectId Mongo stores.

        Necessary because "6a57..." (a string) and ObjectId("6a57...") do not
        compare equal - querying with the string finds nothing at all.
        """
        try:
            return ObjectId(customer_id)
        except (InvalidId, TypeError) as exc:
            raise InvalidCustomerId(
                f"'{customer_id}' is not a valid customer id"
            ) from exc

    def _run(self, operation):
        """Run a query, translating an unreachable database into our own error."""
        try:
            return operation()
        except ServerSelectionTimeoutError as exc:
            raise DatabaseUnavailable(
                f"Cannot reach MongoDB at {database.MONGO_URI}. "
                "Is the container running?"
            ) from exc

    # Setup

    def ensure_indexes(self):
        """
        Enforce unique emails in the database itself.

        The closest thing here to a SQL constraint: it holds even if a bug slips
        past the service's validation, because Mongo refuses the write outright.
        It also makes lookups by email fast rather than a full collection scan.

        create_index is idempotent - running it repeatedly costs nothing.
        """
        self._run(lambda: self._collection.create_index(
            [("email", ASCENDING)], unique=True, name="email_unique"
        ))

    # Queries

    def find_all(self):
        """Every customer, name-sorted so the order is stable between calls."""
        documents = self._run(
            lambda: list(self._collection.find().sort("name", ASCENDING))
        )
        return [Customer.from_document(d) for d in documents]

    def find_by_id(self, customer_id):
        """One Customer, or None if there's no such id."""
        oid = self._object_id(customer_id)
        document = self._run(lambda: self._collection.find_one({"_id": oid}))
        return Customer.from_document(document) if document else None

    def find_by_email(self, email):
        """One Customer by email, or None. Used to check for duplicates."""
        document = self._run(lambda: self._collection.find_one({"email": email}))
        return Customer.from_document(document) if document else None

    # Writes

    def insert(self, customer):
        """Store a new Customer and return it with its assigned id."""
        document = customer.to_document()
        try:
            result = self._run(lambda: self._collection.insert_one(document))
        except DuplicateKeyError as exc:
            raise DuplicateEmail(
                f"A customer with email {customer.email} already exists"
            ) from exc
        customer.id = str(result.inserted_id)
        return customer

    def replace(self, customer_id, customer):
        """
        Replace a stored customer wholesale, returning the new version, or None
        if that id doesn't exist.

        find_one_and_replace does the swap and the read in one atomic round trip,
        so nothing can change underneath us in between.
        """
        oid = self._object_id(customer_id)
        try:
            document = self._run(lambda: self._collection.find_one_and_replace(
                {"_id": oid},
                customer.to_document(),
                return_document=ReturnDocument.AFTER,
            ))
        except DuplicateKeyError as exc:
            raise DuplicateEmail(
                f"A customer with email {customer.email} already exists"
            ) from exc
        return Customer.from_document(document) if document else None

    def delete(self, customer_id):
        """Delete a customer. True if one went, False if the id wasn't there."""
        oid = self._object_id(customer_id)
        result = self._run(lambda: self._collection.delete_one({"_id": oid}))
        return result.deleted_count == 1

    def delete_all(self):
        """Empty the collection. Used by seed.py to reset to a known state."""
        result = self._run(lambda: self._collection.delete_many({}))
        return result.deleted_count
