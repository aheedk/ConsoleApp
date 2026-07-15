"""
Model layer - what a Customer IS.

A plain data structure with no behaviour beyond converting itself to and from the
two shapes it needs to exist in. It imports nothing from the rest of the app,
which is what lets every other layer pass it around freely.

The two conversions are deliberately separate, because the two shapes differ:

    Mongo document          API response
    { _id: ObjectId(...)    { "id": "6a57...",     <- string, renamed
      name: ...               "name": ...,
      email: ...              "email": ...,
      balance: ... }          "balance": ... }
"""

from dataclasses import dataclass


@dataclass
class Customer:
    """
    One customer.

    @dataclass generates __init__, __repr__ and __eq__ from the fields below, so
    Customer(name="X", email="y@z.com") just works, and two customers with equal
    fields compare equal.

    `id` is last and defaults to None because a customer that hasn't been saved
    yet doesn't have one - Mongo assigns it on insert.
    """

    name: str
    email: str
    balance: float = 0.0
    id: str | None = None

    @classmethod
    def from_document(cls, document):
        """
        Build a Customer from a raw Mongo document.

        str() on the _id is what stops an ObjectId from escaping the repository:
        no layer above this one ever handles bson types.
        """
        return cls(
            id=str(document["_id"]),
            name=document["name"],
            email=document["email"],
            balance=document["balance"],
        )

    def to_document(self):
        """
        The shape Mongo stores.

        No id: Mongo owns _id and assigns it. Including it here would try to
        overwrite the primary key.
        """
        return {
            "name": self.name,
            "email": self.email,
            "balance": self.balance,
        }

    def to_dict(self):
        """
        The shape the API hands out.

        Fields are listed explicitly rather than dumped wholesale, so a field
        added to this model later cannot leak into an API response by accident.
        It's a whitelist. `_id` becomes `id` because the underscore is a Mongo
        detail with no place in a public API.
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "balance": self.balance,
        }
