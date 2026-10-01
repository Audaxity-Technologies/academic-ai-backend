class AppException(Exception):
    """Base exception for application-level errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ResourceNotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    pass


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(AppException):
    """Raised when a user lacks permission."""

    pass


class ConflictError(AppException):
    """Raised when an operation conflicts with existing data."""

    pass