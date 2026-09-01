#!/usr/bin/env python3
"""Flatten authorized LightGBM text models into a small pure-Python blob."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import lightgbm as lgb

DEFAULT_FAMILIES = ("main", "c7", "mid", "low", "easy")


def flatten(tree: dict) -> tuple[list[int], list[int], list[int], list[float | None], list[object], list[float]]:
    """Convert one LightGBM tree into parallel arrays for dependency-free scoring."""

    left: list[int] = []
    right: list[int] = []
    feature: list[int] = []
    threshold: list[float | None] = []
    categories: list[object] = []
    values: list[float] = []

    def visit(node: dict) -> int:
        index = len(left)
        left.append(0)
        right.append(0)
        if "leaf_value" in node:
            feature.append(-1)
            threshold.append(0.0)
            categories.append(None)
            values.append(float(node["leaf_value"]))
            return index
        feature.append(int(node["split_feature"]))
        if node.get("decision_type") == "==":
            threshold.append(None)
            categories.append(
                frozenset(int(float(value)) for value in str(node["threshold"]).split("||"))
            )
        else:
            threshold.append(float(node["threshold"]))
            categories.append(None)
        values.append(0.0)
        left[index] = visit(node["left_child"])
        right[index] = visit(node["right_child"])
        return index

    visit(tree["tree_structure"])
    return left, right, feature, threshold, categories, values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="directory containing family.txt files")
    parser.add_argument("--output", type=Path, required=True, help="output pickle path")
    parser.add_argument("--families", default=",".join(DEFAULT_FAMILIES))
    args = parser.parse_args()
    families = tuple(item.strip() for item in args.families.split(",") if item.strip())
    if not families:
        raise ValueError("at least one family is required")
    models: dict[str, list[tuple]] = {}
    feature_count: int | None = None
    stats: dict[str, dict[str, int]] = {}
    for family in families:
        source = args.input_dir / f"{family}.txt"
        if not source.is_file():
            raise FileNotFoundError(source)
        booster = lgb.Booster(model_file=str(source))
        feature_count = feature_count or int(booster.num_feature())
        if int(booster.num_feature()) != feature_count:
            raise ValueError("all family models must use the same feature count")
        trees = [flatten(tree) for tree in booster.dump_model()["tree_info"]]
        models[family] = trees
        stats[family] = {
            "trees": len(trees),
            "nodes": sum(len(tree[0]) for tree in trees),
        }
        print(f"{family}: trees={stats[family]['trees']} nodes={stats[family]['nodes']}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    blob = {"feature_count": feature_count, "families": list(families), "models": models}
    with args.output.open("wb") as handle:
        pickle.dump(blob, handle, protocol=4)
    print(f"wrote {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
