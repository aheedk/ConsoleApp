"""
Database layer - owns the connection to MongoDB.

The bottom of the stack. It knows how to reach the server and nothing else: no
queries, no collections by name, no business rules. Everything above goes through
here to get at Mongo, and nothing else in the app ever constructs a MongoClient.

Why that matters: the connection settings, the pool, and the timeout are
configured in exactly one place.
"""

import os

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from exceptions import DatabaseUnavailable

# Settings come from the environment with a working local default. Nothing secret
# is involved today (the local container has no password), but when this moves to
# a hosted MongoDB the URI will carry real credentials - and the habit of reading
# it from the environment needs to already be here, not retrofitted after a
# password has been committed. Git history is very hard to scrub.
#
# Port 27018, not Mongo's usual 27017: this machine already runs another MongoDB
# on 27017 (the crm-mongodb container). See docker-compose.yml.
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27018")
DB_NAME = os.environ.get("MONGO_DB", "banking")

# ONE client for the life of the process. MongoClient is thread-safe and keeps its
# own connection pool, so building one per request would create a brand new pool
# every time. Note this line does NOT connect - MongoClient is lazy and doesn't
# touch the network until the first real operation.
#
# serverSelectionTimeoutMS defaults to 30s, which makes a dead database feel like
# a hang. 5s fails fast enough to be obvious while developing.
_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)


def get_database():
    """The Database object. Doesn't touch the network."""
    return _client[DB_NAME]


def get_collection(name):
    """A Collection object by name. Doesn't touch the network."""
    return get_database()[name]


def ping():
    """
    Prove the database is genuinely reachable.

    Because MongoClient is lazy, constructing it proves nothing - a dead database
    would otherwise announce itself as a confusing timeout inside some random
    request later. api.py calls this at startup so it fails immediately instead.
    """
    try:
        _client.admin.command("ping")
    except ServerSelectionTimeoutError as exc:
        raise DatabaseUnavailable(
            f"Cannot reach MongoDB at {MONGO_URI}. Is the container running?"
        ) from exc
