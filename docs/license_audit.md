# LICENSE / IP / public-release audit

Audit date: **September 1, 2026 UTC**. This is a conservative engineering
classification, not legal advice. Where permission is not explicit, the
release disposition is to exclude the artifact.

## Governing sources checked

The audit used the competition Rules page retrieved from Kaggle, the Kaggle
Staff discussion about `ptcg_engine.zip`, and the README/license shipped with
the local engine package. The Rules identify the data access scope as
competition-only, limit Competition Data and Pokémon Elements to competition
purposes, require deletion of Competition Data after the competition, and
separately restrict use of models trained on Pokémon Elements outside
participation. The engine notice says the package is not open source, is for
building/testing entries during the competition, and must not be republished.

The winner-license language requires an OSI-approved license for eligible
winning source, but explicitly does not require publishing incompatible input
data or pretrained models. That obligation does not override the separate
Competition Data/Pokémon Elements restrictions.

## Definitions used

| category | audit treatment |
|---|---|
| Original algorithm source | Generic code authored by us that does not embed restricted game assets or a runtime. |
| Competition Data | Replay files, leaderboard exports, supplied tables, indices, and derived rows. |
| Pokémon Elements | Game/card rules, names, identifiers, deck recipes, metadata, assets, and derivatives covered by the Rules. |
| Official runtime | `cg` / `ptcg_engine` package, native binaries, wrappers, and code derived from it. |
| Trained model | Any model trained using restricted Competition Data or Pokémon Elements. |
| Deck/card artifacts | Exact deck files, card IDs, card tables, schemas, or metadata. |
| Replay-derived artifacts | Teacher indices, feature caches, labels, score-bearing fixtures, and similar outputs. |

## File-level classification

The first column records the conservative classification of the artifact as it
existed before this audit. The final column records what remains in the public
release directory.

| path/category | classification | final disposition |
|---|---|---|
| `README.md` | SAFE_AFTER_REDACTION | retained; rewritten to state the license boundary and avoid data-download instructions |
| `LICENSE` | SAFE_AFTER_REDACTION | retained; MIT scope limited to included original files |
| `THIRD_PARTY_NOTICES.md` | SAFE_AFTER_REDACTION | retained; explicit no-license notice for Pokémon materials/runtime/model |
| `requirements.txt` | SAFE_TO_PUBLISH | retained; only NumPy and LightGBM |
| `pyproject.toml` | SAFE_TO_PUBLISH | retained; generic package metadata |
| `configs/bronze_solution.json` | SAFE_AFTER_REDACTION | replaced by `configs/bronze_method.example.json`; no IDs, deck, model, or data paths |
| `models/bronze_ranker.pkl` | DO_NOT_PUBLISH | removed; historical SHA and statistics recorded in provenance |
| `models/bronze_ranker.schema.json` | DO_NOT_PUBLISH | removed; schema/card-derived bytes are not released |
| `models/README.md` | SAFE_TO_PUBLISH | retained as an exclusion notice |
| `submission/deck.csv` | DO_NOT_PUBLISH | removed; exact deck/card identifiers are not released |
| `submission/main.py` | DO_NOT_PUBLISH | removed; embeds the deck, card-aware adapter, and runtime import |
| `submission/README.md` | SAFE_TO_PUBLISH | retained as a boundary notice |
| `src/ptcg_solution/features.py` | DO_NOT_PUBLISH | removed; contains card metadata, identifiers, and runtime-derived logic |
| `src/ptcg_solution/ranker.py` | SAFE_AFTER_REDACTION | replaced by generic pure scorer and stable selector |
| `src/ptcg_solution/runtime.py` | DO_NOT_PUBLISH | removed; locates/imports the restricted runtime |
| `src/ptcg_solution/feature_contract.py` | SAFE_TO_PUBLISH | retained; validates only a generic fixed-width numeric matrix |
| `scripts/train_ranker.py` | SAFE_AFTER_REDACTION | rewritten to consume caller-authorized generic NPZ rows |
| `scripts/export_pure_model.py` | SAFE_AFTER_REDACTION | rewritten with explicit caller paths and no default artifact |
| `scripts/check_model_parity.py` | SAFE_AFTER_REDACTION | generic LightGBM/pure-tree comparison only |
| `scripts/normalize_entrypoint.py` | SAFE_TO_PUBLISH | retained; generic AST utility |
| `scripts/fetch_competition_assets.py` | DO_NOT_PUBLISH | removed; would facilitate restricted downloads |
| `scripts/build_teacher_index.py` | DO_NOT_PUBLISH | removed; parses replay/leaderboard data |
| `scripts/prepare_rows.py` | DO_NOT_PUBLISH | removed; card/runtime-dependent feature generation |
| `scripts/build_submission.py` | DO_NOT_PUBLISH | removed; packages deck/model/official runtime |
| `scripts/validate_submission.py` | DO_NOT_PUBLISH | removed; validates restricted deck/model/archive schema |
| `scripts/run_local.py` | DO_NOT_PUBLISH | removed; imports and executes the official engine |
| `scripts/package_source.py` | SAFE_TO_PUBLISH | retained; failing-closed allowlisted source packager |
| `data/raw/*` | DO_NOT_PUBLISH | excluded; only `.gitkeep` remains |
| `data/processed/*` | DO_NOT_PUBLISH | excluded; only `.gitkeep` remains |
| `docs/*` | SAFE_AFTER_REDACTION | retained after removing operational download/reproduction claims |
| `licenses/JUN_MORITA_MIT.txt` | SAFE_TO_PUBLISH | retained license notice |
| `tests/*` | SAFE_AFTER_REDACTION | rewritten to use synthetic rows and no restricted assets |

## Artifact-specific decisions

### Historical trained model

The historical pure-tree pickle was trained on Competition Data/Pokémon
Elements. Although the Rules distinguish participant-created model weights from
Pokémon Elements, they also restrict use of models trained on Pokémon Elements
outside participating in the Competition and exclude incompatible pretrained
models from the winner open-source grant. No explicit post-competition
redistribution permission was found. The model is therefore **EXCLUDED**, not
MIT-licensed or offered as a download.

### Exact deck

The real deck file contains the competition's card/deck identifiers and recipe.
The Rules' Pokémon Elements definition expressly covers card/game
configuration and deck-construction data. The real file is therefore
**EXCLUDED**. A placeholder is not included because it could be mistaken for a
valid competition deck.

### Source adapters and feature schema

The old feature extractor embeds card identifiers, card metadata, and imports
the official runtime. It is not treated as generic original source. Only the
model-independent row contract and tree-ranking utilities remain.

## Audit conclusion

The public tree is intentionally a methodological source release. It does not
claim full post-competition reproduction, does not distribute Pokémon
Elements/Competition Data/runtime/model/deck, and does not grant rights in any
excluded material. Any future use of external assets requires an independent
authorization review.
