"""
Error template module for structured error handling.
"""

from enum import Enum


class ErrorCategory(str, Enum):
    """
    High level error categories
    """

    CONFIGURATION = "configuration"
    DATA_FETCH = "data fetch"
    IMPACT_FRAMEWORK = "impact framework"


class ErrorTemplate:
    """
    Template for structured error messages with context and suggestions.
    """

    def __init__(
        self,
        category: ErrorCategory,
        user_message: str,
        suggestions: list[str] | None,
        context: dict[str, any],
    ):
        self.category = category
        self.message = user_message
        self.suggestions = suggestions
        self.context = context

    def to_string(self) -> str:
        """
        Converts the error template to a formatted string representation.
        """
        lines = [f"{self.message}"]
        if self.context:
            lines.append("Context: ")
            for key, value in self.context.items():
                lines.append(f" {key}: {value}")
        if self.suggestions:
            lines.append("Suggestions: ")
            for suggestion in self.suggestions:
                lines.append(f" - {suggestion}")
        return "\n".join(lines)


ERRORS: list[ErrorTemplate] = []
