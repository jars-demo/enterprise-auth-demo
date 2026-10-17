"""Role-based access control: roles come from the identity provider, permissions live here."""

PERMISSIONS: dict[str, set[str]] = {
    "viewer": {"invoices:read"},
    "admin": {"invoices:read", "invoices:void"},
}


def can(roles: list[str], permission: str) -> bool:
    """True when any of the user's roles grants the permission. Unknown roles grant nothing."""
    return any(permission in PERMISSIONS.get(role, set()) for role in roles)
