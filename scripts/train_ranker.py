#!/usr/bin/env python3
"""Train grouped option rankers from a caller-supplied NPZ contract.

The input file must contain four arrays:

``X``
    Floating-point matrix with shape ``(rows, features)``.
``y``
    Relevance labels with shape ``(rows,)``.
``qid``
    Query/group identifiers with shape ``(rows,)``.
``family``
    UTF-8 family label for each row with shape ``(rows,)``.

The adapter that creates those rows is deliberately not distributed. Supplying
data is the caller's responsibility, including checking its license.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np

DEFAULT_FAMILIES = ("main", "c7", "mid", "low", "easy")


def _family_value(spec: str, family: str, cast):
    values = {}
    for part in (spec or "").split(","):
        if not part:
            continue
        if "=" not in part:
            return cast(part)
        name, value = part.split("=", 1)
        values[name.strip()] = cast(value)
    return values.get(family, None)


def _load_rows(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        required = {"X", "y", "qid", "family"}
        missing = sorted(required - set(archive.files))
        if missing:
            raise ValueError(f"rows NPZ missing arrays: {missing}")
        X = np.asarray(archive["X"], dtype=np.float32)
        y = np.asarray(archive["y"], dtype=np.float32).reshape(-1)
        qid = np.asarray(archive["qid"]).reshape(-1)
        family = np.asarray(archive["family"]).reshape(-1).astype(str)
    if X.ndim != 2:
        raise ValueError(f"X must be 2-D, got shape {X.shape}")
    n = X.shape[0]
    if any(len(array) != n for array in (y, qid, family)):
        raise ValueError("X, y, qid, and family must have equal row counts")
    if n == 0:
        raise ValueError("rows NPZ is empty")
    return X, y, qid, family


def _group_sizes(qid: np.ndarray) -> np.ndarray:
    if len(qid) == 0:
        return np.empty(0, dtype=np.int32)
    _, counts = np.unique(qid, return_counts=True)
    return counts.astype(np.int32, copy=False)


def _split_by_query(
    X: np.ndarray, y: np.ndarray, qid: np.ndarray, holdout: float
) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray, np.ndarray]]:
    unique = np.unique(qid)
    if len(unique) < 2 or holdout <= 0:
        return (X, y, qid), (X[:0], y[:0], qid[:0])
    n_val = max(1, int(round(len(unique) * holdout)))
    n_val = min(len(unique) - 1, n_val)
    cutoff = unique[-n_val]
    train_mask = qid < cutoff
    val_mask = ~train_mask
    return (X[train_mask], y[train_mask], qid[train_mask]), (X[val_mask], y[val_mask], qid[val_mask])


def train_family(
    X: np.ndarray,
    y: np.ndarray,
    qid: np.ndarray,
    family: str,
    args: argparse.Namespace,
    categorical: list[int],
) -> tuple[lgb.Booster, dict]:
    mask = np.asarray([value == family for value in args._families_source], dtype=bool)
    Xf, yf, qf = X[mask], y[mask], qid[mask]
    if len(Xf) == 0:
        raise ValueError(f"no rows for family {family!r}")
    order = np.argsort(qf, kind="stable")
    Xf, yf, qf = Xf[order], yf[order], qf[order]
    (Xtr, ytr, qtr), (Xva, yva, qva) = _split_by_query(Xf, yf, qf, args.holdout)
    if len(Xtr) == 0 or len(np.unique(qtr)) == 0:
        raise ValueError(f"family {family!r} has no training queries")
    leaves = _family_value(args.leaves, family, int) or 127
    rate = _family_value(args.learning_rate, family, float) or 0.04
    min_leaf = _family_value(args.min_data_in_leaf, family, int) or 100
    params = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "ndcg_eval_at": [1],
        "learning_rate": rate,
        "num_leaves": leaves,
        "min_data_in_leaf": min_leaf,
        "feature_fraction": args.feature_fraction,
        "bagging_fraction": args.bagging_fraction,
        "bagging_freq": 1 if args.bagging_fraction < 1 else 0,
        "lambdarank_truncation_level": args.truncation,
        "verbosity": -1,
        "seed": args.seed,
        "bagging_seed": args.seed + 1,
        "feature_fraction_seed": args.seed + 2,
        "num_threads": args.threads,
    }
    train_set = lgb.Dataset(Xtr, label=ytr, group=_group_sizes(qtr), categorical_feature=categorical)
    valid_sets = [train_set]
    callbacks = []
    if len(Xva):
        valid_set = lgb.Dataset(Xva, label=yva, group=_group_sizes(qva), reference=train_set)
        valid_sets.append(valid_set)
        callbacks.append(lgb.early_stopping(args.early_stopping_rounds, verbose=False))
    started = time.time()
    booster = lgb.train(params, train_set, num_boost_round=args.rounds, valid_sets=valid_sets, callbacks=callbacks)
    report = {
        "family": family,
        "features": int(X.shape[1]),
        "training_rows": int(len(Xtr)),
        "validation_rows": int(len(Xva)),
        "training_groups": int(len(np.unique(qtr))),
        "validation_groups": int(len(np.unique(qva))),
        "trees": int(booster.current_iteration()),
        "num_leaves": leaves,
        "learning_rate": rate,
        "min_data_in_leaf": min_leaf,
        "seconds": round(time.time() - started, 3),
    }
    return booster, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, required=True, help="caller-supplied authorized rows.npz")
    parser.add_argument("--out-dir", type=Path, required=True, help="directory for LightGBM text models")
    parser.add_argument("--families", default=",".join(DEFAULT_FAMILIES))
    parser.add_argument("--rounds", type=int, default=900)
    parser.add_argument("--holdout", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--threads", type=int, default=0)
    parser.add_argument("--learning-rate", default="0.04", help="number or family=value pairs")
    parser.add_argument("--leaves", default="127", help="number or family=value pairs")
    parser.add_argument("--min-data-in-leaf", default="100", help="number or family=value pairs")
    parser.add_argument("--feature-fraction", type=float, default=0.8)
    parser.add_argument("--bagging-fraction", type=float, default=0.8)
    parser.add_argument("--truncation", type=int, default=12)
    parser.add_argument("--early-stopping-rounds", type=int, default=40)
    parser.add_argument("--categorical-indices", default="", help="comma-separated zero-based column indices")
    args = parser.parse_args()
    args._families_source = None
    X, y, qid, family = _load_rows(args.rows)
    args._families_source = family
    families = tuple(item.strip() for item in args.families.split(",") if item.strip())
    if not families:
        raise ValueError("at least one family is required")
    categorical = [int(item) for item in args.categorical_indices.split(",") if item.strip()]
    if any(index < 0 or index >= X.shape[1] for index in categorical):
        raise ValueError("categorical index is outside the feature matrix")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    reports = {}
    for name in families:
        booster, report = train_family(X, y, qid, name, args, categorical)
        booster.save_model(str(args.out_dir / f"{name}.txt"))
        reports[name] = report
        print(
            f"{name}: rows={report['training_rows']}+{report['validation_rows']} "
            f"groups={report['training_groups']}+{report['validation_groups']} "
            f"trees={report['trees']}",
            flush=True,
        )
    summary = {
        "rows": int(len(X)),
        "features": int(X.shape[1]),
        "families": list(families),
        "seed": args.seed,
        "rounds": args.rounds,
        "reports": reports,
    }
    (args.out_dir / "report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
