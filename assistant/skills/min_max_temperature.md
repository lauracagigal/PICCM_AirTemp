## Skill: Min / Max Temperature (notebook `b_min_max_temperature.ipynb`)

### Purpose
Quantify and visualize the annual minimum (`TMIN`) and maximum (`TMAX`) temperature trends at the site's GHCN station, plus the diurnal range (`diff = TMAX − TMIN`).

### Required inputs
- A valid site config JSON (`data/sites/<site>.json`).
- The cleaned per-station pickle (`data/air_temp/GHCN_<ghcn_station_id>.pkl`).

### Workflow
1. Load config and build `site_output_dir = Path('../../outputs') / build_site_tag(...)`.
2. Load the cached pickle: `st_data = pd.read_pickle(...)`. Verify columns `TMIN`, `TMAX`, `TMEAN`, `diff` and a `DatetimeIndex`.
3. Keep a daily copy: `st_data_daily = st_data.copy()`. Sanity print: `st_data_daily.TMIN.mean(), st_data_daily.TMAX.mean()`.
4. Daily series figures (plotly interactive, last decade shown by default):
   - `plot_timeseries_interactive([{'data': st_data_daily, 'var': 'TMAX', 'ax': 1, 'label': 'TMAX'}], trendline=False)`.
   - Same for `'TMIN'`.
5. Annual aggregation: `st_data = st_data.resample('YE').mean()` (annual mean of the daily values).
6. Annual figures with trend (plotly):
   - `plot_timeseries_interactive([{'data': st_data, 'var': 'TMIN', 'ax': 1, 'label': 'TMIN'}], trendline=True, ...)` → `F3_ST_min`.
   - Same for `'TMAX'` → `F3_ST_max`.
   - Combined: `[{'var': 'TMIN', ...}, {'var': 'TMAX', ...}]` → `F3_ST_min_max`. Helper returns `(fig, TRENDS)` where `TRENDS` holds the per-variable trend metadata.
7. Diurnal range:
   - `plot_timeseries_interactive([{'data': st_data, 'var': 'diff', 'ax': 1, 'label': 'Difference TMAX - TMIN'}], trendline=True)`.
8. Persist results in `site_output_dir`:
   - `F3_ST_min_<site_tag>.html` + `.png`.
   - `F3_ST_max_<site_tag>.html` + `.png`.
   - `F3_ST_min_max_<site_tag>.html` + `.png`.
   - `T_minmax_summary_metrics_<site_tag>.json` with: TMIN trend (°C/decade), TMAX trend (°C/decade), diurnal-range trend (°C/decade), TMIN/TMAX annual mean (°C), `station_id`, `country`, `period`.

### Reporting style
- "Annual mean TMIN trend at <station_id> (<start>–<end>): X °C/decade. Annual mean TMAX trend: Y °C/decade. Diurnal range trend: Z °C/decade. Source: GHCN-Daily."
- Always report TMIN and TMAX trends together (asymmetric warming is a key climate-monitoring indicator).
- Always state the analysis window and station ID.

### Hard rules
- Do NOT re-download GHCN data here; always read the cached pickle.
- Do NOT inline `plotly.graph_objects` figures; use `plot_timeseries_interactive(...)`.
- The combined min/max figure must use a shared y-axis so the magnitude of TMIN and TMAX trends can be compared visually.
- Do not drop or clip values manually (e.g. `st_data.loc[st_data.TMEAN < 50]`) — that responsibility belongs to `00_site_setup.ipynb`.
