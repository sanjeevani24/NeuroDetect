"""Domain-specific exceptions for the Memory Recall game."""


class MemoryGameError(Exception):
    """Base class for all memory-game domain errors."""


class IncompleteGameDataError(MemoryGameError):
    """
    Raised when the event stream is missing data required to compute a
    feature (e.g. no delayed-recall response was ever submitted, so
    recall_latency cannot be derived). This must never be silently
    converted into a zero — the caller is expected to surface a 4xx.
    """


class InvalidEventSequenceError(MemoryGameError):
    """Raised when required phases are missing or events are inconsistent."""


class FeatureValidationError(MemoryGameError):
    """Raised when a derived feature fails its business-rule range check."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class DuplicateCompletionError(MemoryGameError):
    """Raised when a memory_results row already exists for this assessment."""


class AssessmentNotFoundError(MemoryGameError):
    """Raised when the referenced assessment_id does not exist."""
