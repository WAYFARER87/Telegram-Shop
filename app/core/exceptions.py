"""Application exceptions."""


class AppError(Exception):
    """Base application error."""


class NotFoundError(AppError):
    """Entity was not found."""


class ConflictError(AppError):
    """Conflict with current resource state."""


class ValidationError(AppError):
    """Business validation error."""
