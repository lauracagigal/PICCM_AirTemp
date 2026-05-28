# PICCM_AirTemp

Land surface air-temperature indicators for the **Pacific Islands Climate Change Monitor (PICCM)**. This repository turns daily station data from NOAA's GHCN-Daily archive into the historical air-temperature panels of the PICCM matrix (mean temperature trend, minimum / maximum temperature trends, hot days and cold nights), one Pacific Island site at a time.

It is the air-temperature counterpart of [`PICCM_SeaLevel`](https://github.com/lauracagigal/PICCM_SeaLevel) and shares the same conventions (per-site JSON config, site-tagged outputs, plotting helpers from the sibling [`indicators_setup`](https://github.com/lauracagigal/indicators_setup) repository).

## Indicators
- **Mean surface temperature** — annual mean trend and anomaly vs the WMO 1961–1990 reference period, with ENSO (ONI) modulation.
- **Minimum / maximum temperature** — annual TMIN / TMAX trends and diurnal range (`TMAX − TMIN`).
- **Hot days and cold nights** — WMO/ETCCDI TX90p / TN10p exceedance rates against the 1961–1990 climatology, plus a simpler fixed-percentile variant.

## Workflow
1. **`notebooks/historical/00_site_setup.ipynb`** — interactive site definition: enter `(site_name, lon, lat, country)`; the notebook resolves the GHCN country code, ranks the nearest stations by great-circle distance, lets you pick one, downloads the daily series, applies a light 5σ outlier filter and a 75 % time-completeness filter, and caches the cleaned series.
2. **`notebooks/historical/a_mean_temperature.ipynb`** — annual mean, trend, anomaly + ENSO panel.
3. **`notebooks/historical/b_min_max_temperature.ipynb`** — TMIN, TMAX and diurnal range.
4. **`notebooks/historical/c_hot_cold_days.ipynb`** — ETCCDI hot days / cold nights and fixed-percentile variants.

The download happens **once** in `00_site_setup`; notebooks `a`, `b`, `c` only `pd.read_pickle(...)` the cleaned per-station file.

## Repository layout
```
PICCM_AirTemp/
├── notebooks/historical/      # 00, a, b, c notebooks + surface_temperature.md (Jupyter Book entry)
├── functions/
│   ├── air_temp.py            # site config I/O, build_site_tag, haversine_km
│   ├── temp_func.py           # ETCCDI TX90p / TN10p helpers (centered_percentile, ...)
│   └── data_downloaders.py    # GHCN, ONI, completeness QC, and other downloaders
├── data/
│   ├── sites/<site>.json      # per-site configuration (input)
│   └── air_temp/GHCN_<station_id>.pkl   # cleaned per-station daily series (cache)
├── matrix_cc/figures/         # legacy single-site figure outputs (F2_, F3_, F4_)
├── outputs/<site_tag>/        # per-site figures, tables, JSON metrics (target convention)
└── assistant/                 # CIRA assistant instructions (CIRA_role.md + skills/)
```

## Data sources
- **GHCN-Daily** (NOAA NCEI) — country list, station inventory, per-station daily TMIN/TMAX CSVs. Citation: Menne et al. 2012, *J. Atmos. Oceanic Technol.* 29: 897-910.
- **NOAA ONI** — monthly Niño 3.4 anomalies for the ENSO context.

## Conventions
- Sites are tagged with `build_site_tag(site_name, site_lon, site_lat)` (e.g. `palau_lat7p340_lon134p620`).
- All persisted artefacts are named via `build_output_filename(base_name, site_name, site_lon, site_lat, ext)` so multi-site analyses never collide.
- Trends are reported in **°C/decade**; anomalies in **°C** vs the configured reference period; hot-day / cold-night counts in **days/year**.

## Companion AI assistant
The `assistant/` folder holds the training material for **CIRA** (Climate Indicator Report Assistant), a custom GPT specialised in this workflow. See `assistant/README.md` for how to load `CIRA_role.md` and the per-skill files.

## Related repositories
- [`PICCM_SeaLevel`](https://github.com/lauracagigal/PICCM_SeaLevel) — sister repository for sea-level indicators.
- [`indicators_setup`](https://github.com/lauracagigal/indicators_setup) — shared plotting / formatting library (`ind_setup.plotting`, `ind_setup.plotting_int`).
