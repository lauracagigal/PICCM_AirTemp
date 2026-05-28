## Skill: Functions API Reference (`functions/air_temp.py` + `functions/temp_func.py` + `functions/data_downloaders.py`)

This is the single source of truth for what the assistant is allowed to call. If something is missing, ADD a function here — do not inline it in notebooks.

### `functions/air_temp.py` — site config, geo helpers, naming
- `haversine_km(lon1, lat1, lon2, lat2)` → great-circle distance in km. Vectorised; broadcasts over numpy arrays so it can rank an entire station table in one call.
- `save_site_config(config_dict, output_path)` → write a site-configuration dictionary as JSON. Creates the parent directory if missing. Serialises through `pd.Series` to preserve non-ASCII characters.
- `load_site_config(config_path)` → load the JSON produced by `save_site_config` back into a dict. Raises `FileNotFoundError` if the file is missing.
- `build_site_tag(site_name, site_lon, site_lat)` → filesystem-safe tag, e.g. `"palau_lat7p340_lon134p620"`. `m` prefix marks negative coordinates.
- `build_output_filename(base_name, site_name, site_lon, site_lat, ext='png')` → `"<base_name>_<site_tag>.<ext>"`.

### `functions/temp_func.py` — ETCCDI temperature extremes
- `BASE_PERIOD_START = 1961`, `BASE_PERIOD_END = 1990` — base-period constants (do not modify without explicit user request).
- `exceedance_rate_for_base_period(climate_data, variable_name)` → `(exceedance_rates_dict, all_exceedance_data_dict)`. Per-year fraction of days exceeding the day-specific TX90p (`variable_name = "TMAX"`) or below TN10p (`variable_name = "TMIN"`) threshold, restricted to the base period.
- `centered_percentile(date, base_df, variable_name)` → day-of-year percentile threshold using a centred 5-day window across all base-period years. Returns the 90th percentile for `TMAX`, the 10th for `TMIN`.
- `exceedance_rate_for_outbase_period(climate_data, variable_name)` → 366-row DataFrame `(DAY, THRESHOLD)` that can be joined onto any out-of-base period (typically the full record) to count hot days / cold nights. Year 2024 is used as the leap-year placeholder for `DAY`.

### `functions/data_downloaders.py` — raw downloaders
- `GHCN.download_country_codes()` → DataFrame `(Code, Country)` from `ghcnd-countries.txt`.
- `GHCN.get_country_code(country)` → one-row (or zero-row) DataFrame matching `Country == country` exactly. Use a `contains` search on `download_country_codes()` for fuzzy fallback.
- `GHCN.download_stations_info()` → DataFrame with `ID`, `Latitude`, `Longitude`, `Elevation`, `Name` from `ghcnd-stations.txt`. The first two characters of `ID` are the GHCN country code.
- `GHCN.extract_dict_data_var(GHCND_dir, var, df_country_stations)` → `(records, IDS)`. For each station that contains `var`, downloads its CSV, divides TMIN/TMAX/PRCP by 10 (GHCN tenths), and packages it as `{'data': DataFrame[var], 'var': var, 'ax': 1, 'label': f'Station {ID}'}`. `GHCND_dir` is typically `'https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/'`.
- `download_oni_index(p_data)` → NOAA ONI as a monthly DataFrame indexed by month. `-99.9` is converted to NaN.
- `filter_by_time_completeness(df, time_col, month_threshold, year_threshold)` → `(df_filtered, removed_months, removed_years)`. Two-stage completeness QC: drop months with < `month_threshold` of calendar-day coverage, then drop years with < `year_threshold` of valid months.

### Out-of-scope downloaders (do NOT invoke unless the user explicitly asks)
- `download_MLO_CO2_data`, `download_HOT_CO2_data` — atmospheric / ocean CO2.
- `download_ibtracs` — tropical cyclone tracks (use only on explicit request, with a basin filter).
- `download_uhslc_data`, `download_ERDDAP_data` — sea level / generic ERDDAP fetch (these belong to the PICCM_SeaLevel workflow).

### External plotting helpers (`indicators_setup` package, sibling repo)
Imported via `sys.path.append("../../../../indicators_setup")` from notebooks.
- `ind_setup.plotting`:
  - `plot_bar_probs(x, y, ...)` → `(fig, ax, trend)` with linear fit + significance markers (used in `a` for annual bar plots).
  - `plot_bar_probs_ONI(...)`, `add_oni_cat(...)` → ENSO-coloured bar plot.
  - `fontsize` (constant), shared style configuration.
- `ind_setup.plotting_int`:
  - `plot_timeseries_interactive(dict_plot, trendline=False, label_yaxes=..., figsize=...)` → plotly figure (and trend dict when `trendline=True`).
  - `fig_int_to_glue(...)` — helper to feed plotly figures to `myst_nb.glue` for Jupyter Book.
  - `plot_oni_index_th(...)` — ONI time series with thresholds.

### Hard rules
- If a function is needed but missing, add it to the appropriate `functions/` module (calculations) or to `indicators_setup` (figures), then import it in the notebook. Never inline.
- After editing modules, reload them in the active notebook with `import importlib; import air_temp as at_mod; importlib.reload(at_mod)` (or `temp_func`, `data_downloaders`).
- Keep this file in sync: any addition or rename in `functions/` must update the relevant section here.
