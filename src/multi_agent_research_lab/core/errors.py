"""Custom exceptions for the lab."""


class LabError(Exception):
    """Base class for lab-specific errors."""


class ConfigurationError(LabError):
    """Raised when required runtime configuration is missing or invalid."""


class StudentTodoError(LabError):
    """Raised by intentional TODO skeleton code."""
