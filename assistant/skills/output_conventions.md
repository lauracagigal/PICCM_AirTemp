## Skill: Output Conventions

All persisted artifacts (figures, tables, structured results) MUST follow this convention so multi-site analyses never collide.

### Site tag
- Build with `build_site_tag(site_name, site_lon, site_lat)`.
- Format: `<lowercase_alphanum_site>_lat<lat3dec>p<dec>_lon<lon3dec>p<dec>`.
- Examples:
  - Palau (134.620, 7.340) → `palau_lat7p340_lon134p620`.
  - American Samoa (−170.700, −14.275) → `american_samoa_latm14p275_lonm170p700` (`m` prefix marks negative).

### Filenames
- Build with `build_output_filename(base_name, site_name, site_lon, site_lat, ext=...)`.
- Default extensions: `png` (figures), `html` (plotly interactive companion), `csv` (tables), `json` (structured).
- Always pass a stable `base_name` (no timestamps, no run-specific suffixes).

### Folders
- All NEW outputs go to `outputs/<site_tag>/`. Create with `Path('../../outputs') / build_site_tag(...)`; ensure `mkdir(parents=True, exist_ok=True)`.
- Legacy single-site figures still live in `matrix_cc/figures/` (`F2_*`, `F3_*`, `F4_*`). Do not delete them, but write new artifacts to `outputs/<site_tag>/`.
- Site configuration JSONs live in `data/sites/<site>.json`. They are inputs, not outputs.
- Cached GHCN pickles live in `data/air_temp/GHCN_<ghcn_station_id>.pkl`. They are caches, not analysis outputs.
- Do NOT write to `data/` (other than `data/sites/` and `data/air_temp/`), the notebook directory, or anywhere outside `outputs/<site_tag>/`.

### Canonical filenames (do not rename)
- Mean temperature (notebook `a`):
  - `F2_ST_Mean_<site_tag>.png` — annual mean temperature with linear trend.
  - `F2_ST_Annomalies_top10_<site_tag>.png` — anomaly bars vs reference period with top-10 warmest years highlighted.
  - `T_mean_summary_metrics_<site_tag>.json` — trend °C/decade, Δ °C over window, ref-period mean °C, top-10 warmest years, ENSO sensitivity (slope °C/°C, r, p).
  - `ENSO_temperature_summary_<site_tag>.csv` — ENSO sensitivity table.
- Min / Max temperature (notebook `b`):
  - `F3_ST_min_<site_tag>.png` + `.html` — TMIN annual series with trend.
  - `F3_ST_max_<site_tag>.png` + `.html` — TMAX annual series with trend.
  - `F3_ST_min_max_<site_tag>.png` + `.html` — combined TMIN/TMAX with shared y-axis.
  - `T_minmax_summary_metrics_<site_tag>.json` — TMIN trend, TMAX trend, diurnal-range (`diff`) trend (all °C/decade with p-values).
- Hot days / Cold nights (notebook `c`):
  - `F4_ST_hot_cold_<site_tag>.png` + `.html` — ETCCDI TX90p/TN10p percentage anomaly with trends.
  - `F4_ST_hot_cold_percentiles_<site_tag>.png` + `.html` — simple percentile counts (q90/q10 over 1961–1991).
  - `T_hot_days_per_year_<site_tag>.csv`, `T_cold_nights_per_year_<site_tag>.csv` — annual counts.
  - `T_hot_cold_summary_metrics_<site_tag>.json` — stats and slopes for both definitions.

### JSON content contract
- Always include `site_name`, `ghcn_station_id`, `ghcn_station_name`, `country`, `period` (`{start, end}`) and the data source (`"GHCN-Daily"` / `"NOAA ONI"`).
- Use floats (no numpy scalars) and ISO date strings.
- Group related metrics into sub-dictionaries (e.g. `etccdi_stats`, `fixed_percentile_stats`) for forward compatibility.

### Hard rules
- Never overwrite a different site's outputs. Always re-derive `site_tag` from the loaded config.
- Never embed a site name into the function name; pass it as a parameter.
- When a notebook adds a new figure, document the filename in this file before merging.
- The cached pickle in `data/air_temp/` is keyed by **station ID**, not site tag (so two sites that share a station can share the cache). The figures and JSON in `outputs/` are keyed by **site tag**.
