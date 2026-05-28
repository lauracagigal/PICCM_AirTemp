## Skill: Mean Temperature (notebook `a_mean_temperature.ipynb`)

### Purpose
Quantify the trend and reference-period anomaly of the annual mean surface temperature at the site's GHCN station, and characterize ENSO modulation using NOAA ONI.

### Required inputs
- A valid site config JSON at `data/sites/<site>.json` (produced by `00_site_setup.ipynb`).
- The cleaned per-station pickle at `data/air_temp/GHCN_<ghcn_station_id>.pkl` (also produced by `00`).

### Workflow
1. Load config: `site_cfg = load_site_config(site_config_path)`. Extract `site_name`, `site_lon`, `site_lat`, `country`, `ghcn_station_id`, `ghcn_station_name`, `vars_interest`, `ref_start`, `ref_end`.
2. Build `site_output_dir = Path('../../outputs') / build_site_tag(site_name, site_lon, site_lat)` and `mkdir(parents=True, exist_ok=True)`.
3. Load the cached station data: `st_data = pd.read_pickle(Path('../../data/air_temp') / f'GHCN_{ghcn_station_id}.pkl')`. Verify it has `TMIN`, `TMAX`, `TMEAN`, `diff` and a `DatetimeIndex`.
4. Annual aggregation: `st_data = st_data.resample('YE').mean()`.
5. Trend on annual mean (`TMEAN`):
   - Static figure: `fig, ax, trend = plot_bar_probs(x=st_data.index.year, y=st_data['TMEAN'].values, ...)` (from `ind_setup.plotting`). The `trend` tuple gives the linear fit and significance.
   - Interactive variant: `plot_timeseries_interactive([{'data': st_data, 'var': 'TMEAN', 'ax': 1, 'label': 'TMEAN'}], trendline=True, ...)` from `ind_setup.plotting_int`.
6. Anomalies vs reference period:
   - `mean_ref = st_data.loc[ref_start:ref_end].TMEAN.mean()`.
   - `st_data['TMEAN_ref'] = st_data['TMEAN'] - mean_ref`.
   - Top-`nevents=10` warmest years overlay via `plot_bar_probs(... nevents=10, ...)`.
7. ENSO context:
   - `df_oni = download_oni_index('https://psl.noaa.gov/data/correlation/oni.data')`.
   - Resample station data to monthly: `st_data_monthly = st_data_daily.resample('M').mean()` (use `st_data_daily` before the annual resample).
   - Join `df_oni['tmin'] = st_data_monthly['TMIN']`, `df_oni['tmax'] = st_data_monthly['TMAX']`.
   - Build the ENSO-coloured bar plot via `add_oni_cat` + `plot_bar_probs_ONI` from `ind_setup.plotting`.
   - Annual aggregation for the scatter: `df_oni.resample('Y').mean()`.
8. Persist results in `site_output_dir`:
   - `F2_ST_Mean_<site_tag>.png` (annual mean + trend).
   - `F2_ST_Annomalies_top10_<site_tag>.png` (anomaly bars vs ref period).
   - `ENSO_temperature_summary_<site_tag>.csv` (ENSO slope, correlation, p-value).
   - `T_mean_summary_metrics_<site_tag>.json` with: trend rate (°C/decade), Δ over window (°C), `mean_ref` (°C), top-10 warmest years, ENSO slope (°C/°C), r, p-value, `station_id`, `country`, `period`.

### Reporting style
- "Annual mean temperature trend at <station_id> <station_name> (<start>–<end>): X °C/decade (Δ Y °C over the window). Source: GHCN-Daily."
- "Top 10 warmest years (anomaly vs <ref_start>–<ref_end>): list of (year, +Δ °C)."
- "ENSO sensitivity (TMEAN vs ONI): S °C/°C, r = R, p = P."
- Always cite the analysis window, station ID, and which JSON in `outputs/<site_tag>/` backs each number.

### Hard rules
- Do NOT re-download GHCN data here; always read the cached pickle. If it's missing, instruct the user to run `00_site_setup.ipynb`.
- Do NOT redefine `plot_bar_probs` or `plot_timeseries_interactive` inline; import them from `ind_setup`.
- Use the `ref_start` / `ref_end` from `site_cfg` (do not hardcode 1961-1990 here).
- The trend reported in the JSON must come from `plot_bar_probs(...)` (or equivalent helper) — never from an ad-hoc `np.polyfit` call.
