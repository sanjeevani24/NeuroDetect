class MMSEError(Exception):
    """Base MMSE domain error."""


class AssessmentNotFoundError(MMSEError):
    """Raised when the assessment does not exist."""


class DuplicateCompletionError(MMSEError):
    """Raised when the MMSE result already exists."""


class InvalidEventSequenceError(MMSEError):
    """Raised when required event flow is missing."""


class IncompleteGameDataError(MMSEError):
    """Raised when the event stream cannot produce the requested features."""


class FeatureValidationError(MMSEError):
    def __init__(self, errors: list[str]):
        super().__init__("MMSE feature validation failed.")
        self.errors = errors


class InvalidAssessmentIdError(MMSEError):
    """Raised when the assessment id is not a valid UUID."""
