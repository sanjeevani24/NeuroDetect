"""Domain exceptions for Trail Making."""


class TrailMakingError(Exception):
    """Base class for Trail Making failures."""


class AssessmentNotFoundError(TrailMakingError):
    """Raised when the supplied assessment_id does not exist."""


class DuplicateCompletionError(TrailMakingError):
    """Raised when Trail Making already exists for this assessment."""


class InvalidAssessmentIdError(TrailMakingError):
    """Raised when the path assessment_id is not a valid UUID."""


class TelemetryValidationError(TrailMakingError):
    """Raised when inbound Trail Making telemetry is malformed."""


class FeatureValidationError(TrailMakingError):
    """Raised when computed Trail Making features are out of bounds."""


class FeatureComputationError(TrailMakingError):
    """Raised when features cannot be reconstructed from the event stream."""
