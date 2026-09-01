#!/usr/bin/env python3
"""Compare a pure-tree export with its LightGBM source models."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ptcg_solution.ranker import load_pure, rank_order, score_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-dir", type=Path, required=True)
    parser.add_argument("--pure", type=Path, required=True)
    parser.add_argument("--rows", type=Path, required=True, help="fixture NPZ with X, y, qid, family")
    parser.add_argument("--families", default="main,c7,mid,low,easy")
    args = parser.parse_args()
    families = tuple(item.strip() for item in args.families.split(",") if item.strip())
    with np.load(args.rows, allow_pickle=False) as archive:
        X = np.asarray(archive["X"], dtype=np.float32)
        y = np.asarray(archive["y"], dtype=np.float32).reshape(-1)
        qid = np.asarray(archive["qid"]).reshape(-1)
        family = np.asarray(archive["family"]).reshape(-1).astype(str)
    if X.ndim != 2 or not (len(y) == len(qid) == len(family) == X.shape[0]):
        raise ValueError("fixture arrays have incompatible shapes")
    pure = load_pure(args.pure)
    worst = 0.0
    ranking_same = ranking_total = 0
    topk_same = topk_total = 0
    top1_same = top1_total = 0
    for name in families:
        indices = np.flatnonzero(family == name)
        if len(indices) == 0:
            continue
        booster = lgb.Booster(model_file=str(args.models_dir / f"{name}.txt"))
        for query in np.unique(qid[indices]):
            current = indices[qid[indices] == query]
            reference = np.asarray(booster.predict(X[current]), dtype=float)
            exported = np.asarray(score_rows(pure, name, X[current].tolist()), dtype=float)
            if len(reference):
                worst = max(worst, float(np.max(np.abs(reference - exported))))
            ref_order = rank_order(reference.tolist())
            got_order = rank_order(exported.tolist())
            ranking_total += 1
            ranking_same += ref_order == got_order
            k = max(1, int(np.count_nonzero(y[current] > 0)))
            ref_top = set(ref_order[:k])
            got_top = set(got_order[:k])
            topk_total += 1
            topk_same += ref_top == got_top
            if k == 1:
                top1_total += 1
                top1_same += ref_top == got_top
    if ranking_total == 0:
        raise SystemExit("PARITY FAILED: no comparable queries")
    print(f"max_score_difference={worst:.6e}")
    print(f"ranking_agreement={ranking_same}/{ranking_total}")
    print(f"top_k_agreement={topk_same}/{topk_total}")
    print(f"top_1_agreement={top1_same}/{top1_total}")
    if ranking_same != ranking_total or topk_same != topk_total:
        raise SystemExit("PARITY FAILED")
    print("PARITY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
