# Reproducibility and release-audit record

Audit date: **September 1, 2026 UTC**.

This release intentionally makes a narrower claim than the competition package:
the public source utilities are installable and testable, while the exact
competition data, deck, trained model, and official engine are excluded. No
new model was trained and no competition submission was made during this audit.

## Executed clean-environment gates

The following commands were executed from a fresh temporary checkout of this
directory with `PYTHONPATH`, competition credentials, and runtime variables
unset:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip --index-url https://pypi.org/simple
python -m pip install --index-url https://pypi.org/simple -r requirements.txt
python -m pip install --index-url https://pypi.org/simple -e .
python -m pip check
python -m unittest discover -s tests -v
python -m compileall -q src scripts tests
python scripts/train_ranker.py --help
python scripts/export_pure_model.py --help
python scripts/check_model_parity.py --help
python scripts/package_source.py --output artifacts/public
```

All commands above completed successfully. The source archive was built from
an explicit allowlist and contains no model, deck, data, engine, archive, or
compiled binary. The final audit archive had 26 members. Archive bytes are
reproducibly generated from the allowlist but may have a different digest when
the filesystem timestamp changes.

## Pipeline boundary

The historical flow was:

```text
competition replay/card assets → private adapter → numeric rows
→ five grouped rankers → pure tree export → competition entrypoint
```

Only the model-independent suffix is public here:

```text
caller-authorized rows.npz → generic training (optional)
→ LightGBM text models → pure export → parity check
```

The first arrow in the historical flow is not reproducible from this repository
because its inputs and runtime are restricted and are not redistributed. The
released model was removed before this audit, so the public tests cannot
silently load it.

## Gate results

| component | result | evidence |
|---|---|---|
| Environment installation | PASS | fresh Python 3.12 virtual environment; `pip check` clean |
| Public source tests | PASS | unittest suite completed without assets |
| Static compilation | PASS | `compileall` completed |
| Training source implementation | AVAILABLE | CLI/help and source audit; no new training run |
| Fresh bronze-model reproduction | BLOCKED | requires excluded competition rows/assets and permissions |
| Generic tree export implementation | AVAILABLE | CLI/help and source audit; no new model generated |
| Generic parity implementation | AVAILABLE | CLI/help and source audit; no fixture/model required |
| Source-only package build | PASS | allowlisted archive generated and inspected |
| Competition data acquisition | EXCLUDED | no downloader or data files in release |
| Feature generation from replays | EXCLUDED | adapter/card/runtime files removed |
| Historical bronze-model inference | EXCLUDED | trained model bytes removed |
| Official engine battle simulation | BLOCKED | runtime is not redistributable and no authorized post-competition runtime was available |
| Full from-scratch bronze reproduction | NOT CLAIMED | would require excluded assets and permissions |

## No hidden historical dependency

The source package allowlist contains only root notices/configuration,
documentation, generic scripts, the generic `ptcg_solution` package, tests,
and empty data placeholders. The model/deck directories contain README files
only. The generic scripts have no imports from an engine package, no fixed
machine paths, no competition credentials, and no default model/deck path.
