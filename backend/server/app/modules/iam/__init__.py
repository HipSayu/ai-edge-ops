"""IAM context: users, authentication, and the role/permission matrix.

The shared foundation every other module's HTTP layer depends on for
authentication and RBAC. Public surface: :class:`UserService`,
:class:`AuthService`, and the auth dependencies in ``bearer_auth`` / ``ws_auth``.
"""

from __future__ import annotations

from app.modules.iam.auth_service import AuthService
from app.modules.iam.user_service import UserService

__all__ = ["AuthService", "UserService"]
