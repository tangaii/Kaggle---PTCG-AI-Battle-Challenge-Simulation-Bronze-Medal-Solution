# Final bronze method (public description)

The final competition package was a deterministic legal-option ranking policy.
For every decision, the private competition adapter created one row per legal
option, selected one of five context families, summed the exported tree scores,
and returned a stable descending-score top-k selection. A short semantic action
history was retained to break otherwise indistinguishable repeated choices.

The historical recipe used 361 columns, LightGBM LambdaRank, five context
families (`main`, `c7`, `mid`, `low`, `easy`), a 900-round ceiling, seed 0, and
family-specific leaf limits. The frozen artifact had 346, 360, 237, 54, and
170 trees respectively. These numbers are provenance, not a promise that the
restricted model or feature schema can be redistributed.

The exact observation adapter, card metadata, deck, replay parser, and official
engine are intentionally absent from the public tree. The files that remain
implement the model-independent contracts: fixed-width numeric rows, grouped
ranking training, LightGBM-tree flattening, pure scoring, stable selection, and
parity checking. This separation permits research on the ranking method without
publishing Pokémon Elements or Competition Data.
