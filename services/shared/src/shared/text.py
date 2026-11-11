from shared.errors import Invalid, NotAllowed


def required_name(value: str | None, what: str) -> str:
    """A trimmed, non-empty name."""
    name = (value or "").strip()
    if not name:
        raise Invalid(f"Tên {what} không được để trống")
    return name


def found[T](entity: T | None, message: str) -> T:
    """The entity, or NotAllowed: unknown ids and out-of-scope ids look the same to the caller."""
    if entity is None:
        raise NotAllowed(message)
    return entity
