"""Auth context: password login, token refresh, session assembly.

Public surface for other modules: :class:`AuthService`.
"""

from __future__ import annotations

from app.modules.auth.service import AuthService

__all__ = ["AuthService"]
