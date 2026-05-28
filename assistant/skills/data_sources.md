## Skill: Data Sources & Attribution

### Land surface temperature — GHCN-Daily (NOAA NCEI)
- Country lookup: `https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-countries.txt`. Fetched via `GHCN.download_country_codes()`.
- Station inventory: `https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt`. Fetched via `GHCN.download_stations_info()`.
- Per-station daily CSVs: `https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/<station_id>.csv`.
- Variables in use:
  - `TMIN` — daily minimum temperature, stored in tenths of °C; the downloader divides by 10. Units returned: °C.
  - `TMAX` — daily maximum temperature, stored in tenths of °C; divided by 10. Units returned: °C.
  - Derived in `00_site_setup.ipynb`: `TMEAN = (TMIN + TMAX) / 2`, `diff = TMAX − TMIN`.
- Sentinels: `-9999` is converted to NaN by `pd.read_csv(na_values=['-9999'])` inside `extract_dict_data_var`.
- Documentation: `https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/doc/GHCND_documentation.pdf`.
- Citation: Menne, M.J., I. Durre, R.S. Vose, B.E. Gleason, and T.G. Houston, 2012. *An overview of the Global Historical Climatology Network-Daily Database.* J. Atmos. Oceanic Technol., 29, 897-910.

### ENSO — NOAA ONI
- URL: `https://psl.noaa.gov/data/correlation/oni.data`.
- Format: monthly Niño 3.4 anomalies. Replace `-99.9` with NaN on load (handled by `download_oni_index`).
- Classification rules (when needed; not provided by `temp_func.py` directly):
  - El Niño when 5 consecutive months of ONI ≥ 0.5.
  - La Niña when 5 consecutive months of ONI ≤ −0.5.
  - Otherwise Neutral.
- Color convention everywhere: El Niño = red, La Niña = blue, Neutral = gray.
- Citation: NOAA Climate Prediction Center / Physical Sciences Laboratory.

### Reference periods
- Climatology baseline for anomalies and ETCCDI thresholds: **1961–1990** (WMO standard). Stored in the site config as `reference_period_start` / `reference_period_end`; hardcoded in `temp_func.py` for the TX90p/TN10p calculation.
- Simple-percentile thresholds (notebook `c`, second section) use **1961–1991** to mirror the legacy reference figures in `matrix_cc/figures/`.

### QC steps applied in `00_site_setup.ipynb`
1. **Outlier filter** — drop rows where any numeric column is more than `threshold_sigma` (default 5) standard deviations from its column mean. Removes obvious sensor glitches (e.g. `TMIN = 500`).
2. **Completeness filter** — `filter_by_time_completeness` with month and year thresholds equal to `completeness_threshold` (default 0.75). A month with < 75% of its calendar days observed is dropped; a year with < 75% of valid months is dropped.

### Optional / out-of-scope data sources
The following exist in `functions/data_downloaders.py` but are NOT part of CIRA's standard PICCM Air Temperature workflow:
- `download_MLO_CO2_data`, `download_HOT_CO2_data` — atmospheric / ocean CO2.
- `download_ibtracs` — tropical cyclone tracks (only on explicit user request with a basin filter).
- `download_uhslc_data`, `download_ERDDAP_data` — sea level / generic ERDDAP fetch (PICCM_SeaLevel workflow).

Only invoke these when the user explicitly asks for them; otherwise stick to GHCN-Daily + ONI.

### Hard rules
- Always attribute the data source in narrative outputs (e.g. "Source: GHCN-Daily station <id>", "Source: NOAA ONI").
- Never present user-uploaded data as primary. If a custom file is provided, ask the user whether it should overlay, replace, or validate the canonical source.
- Never invent GHCN station IDs or country codes; always resolve them through `GHCN.get_country_code(...)` and the site config.
- Always state units (°C, °C/decade, days/yr, °C/°C for ENSO sensitivity) in any numeric statement.
