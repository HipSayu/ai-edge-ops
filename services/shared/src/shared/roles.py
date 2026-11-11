from enum import StrEnum


class Role(StrEnum):
    VIEWER = "VIEWER"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


_RANK = {Role.VIEWER: 0, Role.OPERATOR: 1, Role.ADMIN: 2}


def has_at_least(role: Role, minimum: Role) -> bool:
    return _RANK[role] >= _RANK[minimum]
