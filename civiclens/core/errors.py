class ServiceError(Exception):
    """An expected problem. The message is safe to show to the user."""


class AuthError(ServiceError):
    pass


class PermissionDenied(ServiceError):
    pass


class NotFoundError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


def validation_message(exc) -> str:
    """Turn a pydantic ValidationError into one short line for the user."""
    first = exc.errors()[0]
    field = str(first["loc"][-1]).replace("_", " ").capitalize() if first.get("loc") else "Input"
    return f"{field}: {first['msg']}"
