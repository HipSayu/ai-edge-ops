"""Errors the business rules raise. Nothing here knows HTTP: `shared.http` maps each kind to a status."""


class DomainError(Exception):
    """Base of every expected failure."""


class Unauthenticated(DomainError):
    """Not signed in, bad credentials, or an expired or disabled session."""


class Forbidden(DomainError):
    """Signed in, but the role or cluster scope does not allow this."""


class NotAllowed(DomainError):
    """Unknown id or outside the viewer's scope (the two are not told apart on purpose)."""


class Conflict(DomainError):
    """The request clashes with the current state (full node, duplicate name...)."""


class Invalid(DomainError):
    """The request is understood but its content is not acceptable (bad value, wrong file type...)."""


class ServiceUnavailable(DomainError):
    """A dependency the request needs is not configured or not reachable."""
