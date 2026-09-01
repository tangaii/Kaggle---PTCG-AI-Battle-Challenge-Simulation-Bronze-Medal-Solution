#!/usr/bin/env python3
"""Compare the canonical public entrypoint with a supplied reference snapshot."""
from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path


def normalized_ast(path: Path) -> str:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list):
            body[:] = [item for item in body if not (
                isinstance(item, ast.Expr)
                and isinstance(getattr(item, "value", None), ast.Constant)
                and isinstance(item.value.value, str)
            )]
    return ast.dump(tree, include_attributes=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path, default=Path("submission/main.py"), nargs="?")
    args = parser.parse_args()
    left = normalized_ast(args.reference)
    right = normalized_ast(args.candidate)
    print(f"reference_ast_sha256={hashlib.sha256(left.encode()).hexdigest()}")
    print(f"candidate_ast_sha256={hashlib.sha256(right.encode()).hexdigest()}")
    if left != right:
        print("ENTRYPOINT_AST_EQUIVALENCE=FAIL")
        return 1
    print("ENTRYPOINT_AST_EQUIVALENCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
