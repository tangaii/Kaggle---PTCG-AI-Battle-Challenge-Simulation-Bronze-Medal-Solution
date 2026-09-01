#!/usr/bin/env python3
"""Build an allowlisted source-only archive for public review.

The allowlist intentionally excludes model files, decks, data directories, and
competition/runtime payloads. Failing closed is preferable to accidentally
publishing an artifact whose provenance is unclear.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = (
    ".gitignore",
    "LICENSE",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
    "requirements.txt",
)
ROOT_DIRS = ("configs", "docs", "licenses", "scripts", "src", "tests")
EXTRA_FILES = (
    "data/README.md",
    "data/raw/.gitkeep",
    "data/processed/.gitkeep",
    "models/README.md",
    "submission/README.md",
)
FORBIDDEN_SUFFIXES = {".pkl", ".csv", ".zip", ".tar", ".gz", ".so", ".dll", ".exe", ".bin"}
ABSOLUTE_PATH = re.compile(r"(?m)^(?:/data/|/home/|/tmp/|[A-Za-z]:[\\/])")
# Match assignment-shaped credential markers while avoiding this scanner's own
# constant name.  This is a release hygiene check, not a secret detector.
SECRET = re.compile(r"(?i)(?:api[_-]?key|password|token)\s*[:=]")


def _files() -> list[Path]:
    paths = [ROOT / name for name in ROOT_FILES]
    for directory in ROOT_DIRS:
        paths.extend(
            path
            for path in (ROOT / directory).rglob("*")
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and not any(part.endswith(".egg-info") for part in path.parts)
                and path.suffix != ".pyc"
            )
        )
    paths.extend(ROOT / name for name in EXTRA_FILES)
    unique = {path.resolve() for path in paths}
    return sorted(unique, key=lambda path: path.relative_to(ROOT).as_posix())


def _audit(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        raise ValueError(f"forbidden release suffix: {relative}")
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise ValueError(f"binary payload is not publishable: {relative}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"non-UTF-8 payload is not publishable: {relative}") from exc
    if ABSOLUTE_PATH.search(text):
        raise ValueError(f"author-machine absolute path found in {relative}")
    if SECRET.search(text) and relative not in {"README.md", "THIRD_PARTY_NOTICES.md"}:
        raise ValueError(f"credential-like assignment found in {relative}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "public")
    parser.add_argument("--name", default="option_ranker_source")
    args = parser.parse_args()
    files = _files()
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
        _audit(path)
    args.output.mkdir(parents=True, exist_ok=True)
    archive = args.output / f"{args.name}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for path in files:
            info = tar.gettarinfo(str(path), arcname=path.relative_to(ROOT).as_posix())
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            with path.open("rb") as handle:
                tar.addfile(info, handle)
    with tarfile.open(archive, "r:gz") as tar:
        members = sorted(tar.getnames())
    manifest = {
        "archive": archive.name,
        "sha256": _sha256(archive),
        "member_count": len(members),
        "members": members,
        "restricted_payloads_included": False,
    }
    manifest_path = archive.with_suffix(archive.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
