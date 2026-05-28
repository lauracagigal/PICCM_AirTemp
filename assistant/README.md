# CIRA Assistant — Training Material

This folder holds the instructions used to train an external assistant — **CIRA** (Climate Indicator Report Assistant) — e.g. as a ChatGPT custom GPT. The current skill set specializes CIRA in the PICCM_AirTemp repository workflow.

## How to use
- `CIRA_role.md` — paste the contents into the "Instructions" / system prompt of the assistant. Defines CIRA's identity, scope, conventions, data sources, analysis rules, plotting rules, output naming, and error handling.
- `skills/` — modular workflow-specific instructions. Attach each one as a separate "skill" file (or concatenate them into the assistant's knowledge base):
  - `site_setup.md` — how to run `00_site_setup.ipynb`.
  - `mean_temperature.md` — workflow for `a_mean_temperature.ipynb`.
  - `min_max_temperature.md` — workflow for `b_min_max_temperature.ipynb`.
  - `hot_cold_days.md` — workflow for `c_hot_cold_days.ipynb`.
  - `functions_api.md` — single source of truth for callable functions in `functions/`.
  - `output_conventions.md` — naming and folder rules for figures, CSVs and JSONs.
  - `data_sources.md` — canonical data sources, units, and citations.

## Repository quick map
- `notebooks/historical/` — 4 notebooks (`00`, `a`, `b`, `c`).
- `functions/` — Python modules (site config + geo, temperature extremes, downloaders).
- `data/air_temp/` — cached per-station GHCN pickles (`GHCN_<station_id>.pkl`).
- `data/sites/` — per-site config JSON files.
- `matrix_cc/figures/` — legacy single-site figure outputs.
- `outputs/<site_tag>/` — per-site figures, CSVs, JSONs (target convention for new artifacts).

## Updating the assistant
- When you add or rename a function in `functions/`, update `skills/functions_api.md` in the same PR.
- When you introduce a new persisted artifact (figure/CSV/JSON), document it in `skills/output_conventions.md`.
- When a new analysis notebook is added, mirror its workflow in a new `skills/<name>.md`.
