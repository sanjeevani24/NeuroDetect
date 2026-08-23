from __future__ import annotations


class Model1Error(Exception):
    """Base Model 1 error."""


class Model1ArtifactError(Model1Error):
    """Raised when model artifacts cannot be loaded."""


class Model1FeatureValidationError(Model1Error):
    """Raised when the 47-feature vector is invalid."""

    def __init__(self, message: str, *, feature_name: str | None = None):
        super().__init__(message)
        self.feature_name = feature_name


class Model1IncompleteAssessmentError(Model1Error):
    """Raised when one or more required games are missing."""

    def __init__(self, missing_games: list[str]):
        super().__init__("Cognitive assessment incomplete")
        self.missing_games = missing_games


class Model1PredictionError(Model1Error):
    """Raised when inference returns an invalid result."""


class Model1SchemaNotReadyError(Model1Error):
    """Raised when required Supabase tables for Model 1 have not been applied."""
