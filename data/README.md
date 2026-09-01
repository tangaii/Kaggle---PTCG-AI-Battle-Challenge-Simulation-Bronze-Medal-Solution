# Data boundary

This public release intentionally contains no Competition Data, Pokémon
Elements, replay files, card tables, deck lists, leaderboard exports, teacher
indices, processed rows, or runtime files. The empty directories are present
only to document the layout used during the competition:

```text
data/
├── raw/         # ignored; no files are released here
└── processed/   # ignored; no files are released here
```

The generic training script accepts caller-supplied authorized rows in an
`.npz` file. This repository does not provide a downloader or instructions that
would encourage post-competition use of restricted assets. Anyone attempting
to use external data or a runtime is responsible for obtaining permission and
following the applicable license and competition terms.
