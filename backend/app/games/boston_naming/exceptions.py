"""Domain exceptions for the Boston Naming game."""


class BostonNamingError(Exception):
    """Base class for Boston Naming domain failures."""


class AssessmentNotFoundError(BostonNamingError):
    """Raised when the supplied assessment_id does not exist."""


class DuplicateCompletionError(BostonNamingError):
    """Raised when Boston Naming has already been completed for an assessment."""


class InvalidAssessmentIdError(BostonNamingError):
    """Raised when the path assessment_id is not a valid UUID."""


class TelemetryValidationError(BostonNamingError):
    """Raised when the inbound telemetry stream is malformed."""


class FeatureValidationError(BostonNamingError):
    """Raised when a computed feature is out of the allowed range."""


class FeatureComputationError(BostonNamingError):
    """Raised when the telemetry cannot support deterministic feature extraction."""
