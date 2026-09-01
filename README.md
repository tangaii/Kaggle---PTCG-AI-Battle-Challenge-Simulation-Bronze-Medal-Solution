# Kaggle PTCG AI Battle Challenge Simulation

## 🥉 Bronze Medal Solution — Rank 358 / 6807

**Official source-code release of our Kaggle Bronze Medal solution.**

Due to competition licensing restrictions, this repository does not
redistribute the official competition runtime, Competition Data, Pokémon
Elements, the trained bronze-medal model, or the competition deck.

The public release contains the original method code that can be separated from
those assets: the grouped-ranking training implementation, deterministic
ranking logic, model export/parity tools, configuration examples, tests, and
method documentation. It is a source and methodology release, not a complete
competition submission package and does not claim fully reproducible
from-scratch official battles.

Competition: [The Pokémon Company — PTCG AI Battle Challenge Simulation](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle)

## Installation

The public utilities target Linux and Python 3.12 (Python 3.10–3.12 are
supported). CPU is sufficient; no GPU is required.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip --index-url https://pypi.org/simple
python -m pip install --index-url https://pypi.org/simple -r requirements.txt
python -m pip install --index-url https://pypi.org/simple -e .
```

## Method Overview

The historical bronze policy was a supervised legal-option ranker:

1. The private competition adapter produced one numeric row per legal option.
2. Teacher decisions became grouped ranking labels.
3. Five context-specific LightGBM LambdaRank families were trained.
4. Trees were exported to a dependency-light scorer.
5. Options were sorted by score with a stable original-index tie break.

The historical model used 361 columns and five context families (`main`, `c7`,
`mid`, `low`, and `easy`). The adapter, card metadata, replay reader, deck, and
official runtime are excluded because they are competition-restricted.

## Repository Structure

```text
configs/bronze_method.example.json     redacted method configuration template
data/README.md                         data-layout and licensing boundary
docs/final_solution.md                 public method description
docs/license_audit.md                  file-by-file release classification
docs/provenance.md                     hashes and historical evidence
docs/reproducibility.md                executed source-audit record
licenses/JUN_MORITA_MIT.txt           retained third-party notice
models/README.md                       trained-model exclusion notice
scripts/train_ranker.py                generic LambdaRank trainer
scripts/export_pure_model.py           LightGBM-tree exporter
scripts/check_model_parity.py          pure-vs-LightGBM comparison utility
scripts/normalize_entrypoint.py        generic AST comparison helper
scripts/package_source.py              failing-closed source packager
src/ptcg_solution/ranker.py            pure tree scorer and stable selector
src/ptcg_solution/feature_contract.py  361-column caller-supplied contract
tests/                                 asset-free tests
submission/README.md                   competition-entrypoint/deck notice
```

## Training Pipeline

`scripts/train_ranker.py` implements the generic grouped-ranking stage. It
accepts a caller-supplied NumPy `.npz` file containing:

- `X`: floating-point matrix `(rows, features)`;
- `y`: relevance labels `(rows,)`;
- `qid`: query/group identifiers `(rows,)`;
- `family`: UTF-8 family labels `(rows,)`.

It writes one LightGBM text model and a JSON report per requested family.
Creating the historical rows requires the private competition adapter and
restricted assets, which are not included. Therefore:

```text
Training source implementation = AVAILABLE
Fresh bronze-model reproduction = BLOCKED
```

No new model was trained during the release audit.

## Ranking Method

`ptcg_solution.ranker` operates only on caller-supplied numeric rows and
exported tree blobs. It:

- sums the leaf values along every tree path;
- falls back to an available family if a caller requests an unknown family;
- applies deterministic descending-score ordering;
- breaks ties by the original option index;
- returns the selected indices in their original order.

The module imports no simulator, card table, deck, or competition runtime.

## Feature Contract

`ptcg_solution.feature_contract` validates the model-facing fixed-width
contract. The historical width is 361 columns. The public module intentionally
does not publish the competition-specific feature names, card metadata, or
observation-to-row adapter.

## Export & Parity Tools

`scripts/export_pure_model.py` converts caller-authorized LightGBM text models
to the compact pure-tree representation consumed by `ranker.py`.
`scripts/check_model_parity.py` compares a caller-supplied pure export with its
LightGBM source models on a caller-supplied `.npz` fixture, reporting score,
full-ranking, top-k, and top-1 agreement.

These scripts require explicit input paths and have no default access to a
historical model or data directory.

## Historical Competition Results

| medal | rank | teams |
|---|---:|---:|
| Bronze | 358 | 6,807 |

Historical model statistics and artifact hashes are recorded in
[`docs/provenance.md`](docs/provenance.md). The model and deck bytes are not
released.

## Public Release / Reproducibility Status

| Component | Status |
|---|---|
| Original source code | Included |
| Training implementation | Included |
| Ranking implementation | Included |
| Bronze trained model | Excluded |
| Competition deck | Excluded |
| Competition Data | Excluded |
| Official CG runtime | Excluded |
| Full official battle reproduction | License-blocked |

This table deliberately distinguishes source availability from reproducibility:
the training source is available, while reproducing the historical bronze model
is blocked by the excluded competition assets and permissions.

## Reproducibility Boundary

The audited source-only path is:

```text
fresh clone → install dependencies → run tests/compile
           → inspect generic training/export/parity CLIs
           → build an allowlisted source archive
```

The historical path began with restricted replay/card/runtime assets. Those
inputs, the exact feature adapter, the trained bronze model, the competition
deck, and the official battle engine are not part of this repository. No
post-competition data-download helper is provided, and users are responsible
for any independent authorization of external assets.

## License Notice

The root MIT notice applies only to original source files intentionally retained
in this repository. It does not license Pokémon Elements, Competition Data,
card/deck information, the official competition runtime, competition
submissions, or models trained from restricted materials. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and
[`docs/license_audit.md`](docs/license_audit.md).
