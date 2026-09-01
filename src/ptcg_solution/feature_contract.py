"""Fixed-width numeric feature contract for caller-supplied option rows.

The competition-specific observation adapter is intentionally not part of the
public release. This module documents and validates the model-facing boundary
without embedding any game data, card identifiers, or runtime types.
"""

from __future__ import annotations

from collections.abc import Sequence

DEFAULT_FEATURE_COUNT = 361


class FeatureContractError(ValueError):
    """Raised when caller-supplied rows do not satisfy the public contract."""


def validate_rows(rows: Sequence[Sequence[float]], feature_count: int = DEFAULT_FEATURE_COUNT) -> None:
    """Validate a rectangular option-row matrix.

    ``rows`` may be a list of lists or an array-like object. The function keeps
    dependencies light so it can also be used by a loader before NumPy is
    imported.
    """

    if feature_count <= 0:
        raise FeatureContractError("feature_count must be positive")
    try:
        n_rows = len(rows)
    except TypeError as exc:  # pragma: no cover - defensive branch
        raise FeatureContractError("rows must be a sized 2-D sequence") from exc
    for index, row in enumerate(rows):
        try:
            width = len(row)
        except TypeError as exc:
            raise FeatureContractError(f"row {index} is not a sequence") from exc
        if width != feature_count:
            raise FeatureContractError(
                f"row {index} has {width} features; expected {feature_count}"
            )
    if n_rows == 0:
        return


def feature_count(rows: Sequence[Sequence[float]]) -> int:
    """Return the width of a non-empty rectangular row matrix."""

    if not rows:
        raise FeatureContractError("cannot infer feature count from empty rows")
    width = len(rows[0])
    validate_rows(rows, width)
    return width
