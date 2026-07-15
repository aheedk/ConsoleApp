"""
Domain exceptions - the vocabulary the layers use to report failure.

These live in their own module because every layer needs them, and putting them
anywhere else would create an import cycle.

Note what these are NOT: they carry no HTTP status codes. A service has no
business knowing what a 404 is. The controller owns that mapping - see the
ERROR_STATUS table in controllers.py. That is what keeps the lower layers usable
from somewhere that isn't a web app, like seed.py or a REPL.
"""


class AppError(Exception):
    """Base for everything this application raises deliberately."""


class ValidationError(AppError):
    """Submitted data broke a business rule."""


class InvalidCustomerId(AppError):
    """The given id isn't a well-formed Mongo ObjectId."""


class CustomerNotFound(AppError):
    """No customer exists with that id."""


class DuplicateEmail(AppError):
    """That email already belongs to another customer."""


class DatabaseUnavailable(AppError):
    """MongoDB could not be reached."""
