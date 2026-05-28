## Skill: Site Setup (notebook `00_site_setup.ipynb`)

### Purpose
Define a new analysis site interactively, pick the right GHCN-Daily station, and pre-download + clean the daily time series ONCE, so every other notebook (`a/b/c`) only loads cached data.

### Inputs the assistant must collect
- `site_name` (display name).
- `site_lon`, `site_lat` (decimal degrees; longitudes in `(-180, 180]`).
- `country` (free-form; the notebook fuzzy-matches against the GHCN country list).
- Optional `ghcn_station_id` override. If absent, the closest GHCN station for the country is chosen.
- `vars_interest` (default `["TMIN", "TMAX"]`; other GHCN variables like `"TAVG"` or `"PRCP"` allowed).
- `reference_period_start` / `reference_period_end` (default `"1961"` / `"1990"`).
- `completeness_threshold` (default `0.75`).
- `threshold_sigma` for the outlier filter (default `5.0`).

### Workflow
1. **Step 1 — Site identity**: write `site_name`, `site_lon`, `site_lat`, `country` into the first parameter cell.
2. **Step 2 — Country code**: `GHCN.get_country_code(country)`. If no exact match, show `df_countries[df_countries["Country"].str.contains(country, case=False)]` as suggestions and ask the user to refine the spelling.
3. **Step 3 — Nearest stations**: `GHCN.download_stations_info()` → filter by country code → compute `haversine_km` to `(site_lon, site_lat)` → display the 15 closest stations with `ID`, `Name`, `Latitude`, `Longitude`, `Elevation`, `distance_km`.
4. **Step 4 — Station pick**: set `ghcn_station_id` to one of the listed `ID` values (default index 0 = nearest). The `ghcn_station_name` is filled from the table.
5. **Step 5 — Analysis parameters**: set `vars_interest`, `reference_period_start`/`_end`, `completeness_threshold`.
6. **Step 6 — Save site JSON**: `save_site_config(site_config, Path('../../data/sites/<safe_name>.json'))` where `<safe_name>` is the slugified `site_name`.
7. **Step 7 — Download & cache**:
   - `pickle_path = Path('../../data/air_temp') / f"GHCN_{ghcn_station_id}.pkl"`.
   - If `pickle_path.exists()` and `force_redownload` is False, just `pd.read_pickle(pickle_path)`.
   - Otherwise loop over `vars_interest`, call `GHCN.extract_dict_data_var(GHCND_dir, var, df_target)`, concat the per-variable frames, drop NaN rows, derive `diff = TMAX − TMIN` and `TMEAN = (TMIN + TMAX)/2` when both are present, and save to `pickle_path`.
8. **Step 8 — Outlier filter (5σ)**: for each numeric column, drop rows where `|x − mean| > threshold_sigma * std`. Print which values were removed per column. Overwrite the pickle.
9. **Step 9 — Completeness filter**: `filter_by_time_completeness(st_data, month_threshold=completeness_threshold, year_threshold=completeness_threshold)`. Print the removed months and years. Overwrite the pickle.
10. **Step 10 — Quick-look plot**: one matplotlib subplot per column of `st_data` with the daily series and overlaid monthly + annual means (sanity check only; not a published figure).

### Output contract
- A JSON file at `data/sites/<safe_name>.json` containing: `site_name`, `site_lon`, `site_lat`, `country`, `ghcn_station_id`, `ghcn_station_name`, `vars_interest`, `reference_period_start`, `reference_period_end`, `completeness_threshold`.
- A cleaned pickle at `data/air_temp/GHCN_<ghcn_station_id>.pkl`, DataFrame indexed by `DatetimeIndex` (`DATE`), columns including the requested variables plus `diff` and `TMEAN` (when both TMIN and TMAX are present).

### Common follow-up actions for the assistant
- Confirm which station was selected and the distance from the user-provided coordinates. If `station_distance_km` > 100 km, warn the user.
- If multiple stations are equally close, prefer the one with the longer record (the user can inspect `extract_dict_data_var` output for date coverage).
- After saving the config, recommend opening `a_mean_temperature.ipynb` next.

### Hard rules
- Do not run `00_site_setup.ipynb` automatically more than once unless the user changes the site or the cached pickle is missing.
- Never write site config files outside `data/sites/`.
- Never write GHCN pickles outside `data/air_temp/`, and always name them `GHCN_<ghcn_station_id>.pkl` (per-station, not per-site, so switching stations preserves prior downloads).
- Never change `ghcn_station_id` after it has been written — create a new config (different `<safe_name>.json`) for a new station instead.
