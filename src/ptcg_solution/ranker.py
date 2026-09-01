"""Pure tree scoring and deterministic top-k selection.

The functions operate only on caller-supplied numeric rows and exported tree
blobs. They do not import a simulator, know a deck, or assume any card schema.
"""

from __future__ import annotations

import pickle
from collections.abc import Iterable, Sequence
from pathlib import Path


def load_pure(path: str | Path) -> dict:
    """Load a caller-supplied pure-tree pickle.

    Pickle is executable serialization. Only load files obtained from a trusted
    source and whose license permits the intended use.
    """

    with Path(path).open("rb") as handle:
        blob = pickle.load(handle)
    if not isinstance(blob, dict) or not isinstance(blob.get("models"), dict):
        raise ValueError("not a pure tree model")
    return blob


def score_rows(pure: dict, family: str, rows: Iterable[Sequence[float]]) -> list[float]:
    """Return one additive tree score for each option row."""

    trees = pure.get("models", {}).get(family)
    if trees is None:
        families = sorted(pure.get("models", {}))
        if not families:
            raise ValueError("pure model contains no families")
        trees = pure["models"][families[-1]]

    scores: list[float] = []
    for row in rows:
        total = 0.0
        for left, right, feature, threshold, categories, values in trees:
            node = 0
            while True:
                split = int(feature[node])
                if split < 0:
                    total += float(values[node])
                    break
                threshold_value = threshold[node]
                if threshold_value is None:
                    allowed = categories[node] or frozenset()
                    node = left[node] if int(row[split]) in allowed else right[node]
                else:
                    node = left[node] if row[split] <= threshold_value else right[node]
        scores.append(total)
    return scores


def select_top_k(scores: Sequence[float], minimum: int, maximum: int) -> list[int]:
    """Select a stable top-k set and return indices in original order."""

    n_options = len(scores)
    if n_options == 0:
        return []
    lo = max(0, int(minimum))
    hi = min(n_options, max(0, int(maximum)))
    if hi < lo:
        raise ValueError(f"invalid selection range: minimum={minimum}, maximum={maximum}")
    k = hi
    order = sorted(range(n_options), key=lambda index: (-float(scores[index]), index))
    return sorted(order[:k])


def rank_order(scores: Sequence[float]) -> list[int]:
    """Return the full stable descending ranking of option indices."""

    return sorted(range(len(scores)), key=lambda index: (-float(scores[index]), index))
