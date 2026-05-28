## Skill: Hot Days & Cold Nights (notebook `c_hot_cold_days.ipynb`)

### Purpose
Quantify the annual count and percentage anomaly of **hot days** (TX90p — `TMAX` above the 90th percentile of the 1961–1990 climatology) and **cold nights** (TN10p — `TMIN` below the 10th percentile of the same base period), plus a simpler percentile-based count using fixed quantiles over `1961`-`1991`.

### Required inputs
- A valid site config JSON (`data/sites/<site>.json`).
- The cleaned per-station pickle (`data/air_temp/GHCN_<ghcn_station_id>.pkl`).

### Definitions (ETCCDI / WMO)
- **TX90p (hot day)**: a calendar day on which `TMAX` exceeds the 90th percentile threshold computed from a centred 5-day window across the 1961–1990 base period for the same calendar day.
- **TN10p (cold night)**: same as above, with `TMIN` and the 10th percentile (below instead of above).
- The base period is hardcoded in `temp_func.py` (`BASE_PERIOD_START = 1961`, `BASE_PERIOD_END = 1990`). Do not change without explicit user request.

### Workflow
1. Load config and the cached pickle. Build `site_output_dir = Path('../../outputs') / build_site_tag(...)`.
2. Add the day-of-year key the climatology functions need:
   - `st_data['DATE'] = st_data.index`.
   - `st_data['DAY'] = pd.to_datetime("2024-" + st_data['DATE'].dt.strftime('%m-%d'), format='%Y-%m-%d')`.
3. Daily copy: `st_data_daily = st_data.copy()`.
4. **ETCCDI exceedance thresholds**:
   - `exceed_rates_TMAX = exceedance_rate_for_outbase_period(st_data, "TMAX")` → 366-row DataFrame `(DAY, THRESHOLD)`.
   - `exceed_rates_TMIN = exceedance_rate_for_outbase_period(st_data, "TMIN")`.
5. Apply thresholds to the full record:
   - `TMAX_dict = dict(zip(exceed_rates_TMAX['DAY'], exceed_rates_TMAX['THRESHOLD']))` and similar for TMIN.
   - `df_exceed['THRESHOLD_TMAX'] = df_exceed['DAY'].map(TMAX_dict)`.
   - `df_exceed['HOT_DAY'] = df_exceed['TMAX'] > df_exceed['THRESHOLD_TMAX']`.
   - `df_exceed['THRESHOLD_TMIN'] = df_exceed['DAY'].map(TMIN_dict)`.
   - `df_exceed['COLD_NIGHT'] = df_exceed['TMIN'] < df_exceed['THRESHOLD_TMIN']`.
6. Base-period anomaly rates:
   - `ex_cold, all_cold = exceedance_rate_for_base_period(st_data, "TMIN")`.
   - `ex_hot, all_hot = exceedance_rate_for_base_period(st_data, "TMAX")`.
   - These provide the per-year rate over 1961–1990 used to centre the percentage anomaly.
7. Annual aggregation:
   - For each year, count `HOT_DAY` and `COLD_NIGHT` and divide by the base-period mean (`ex_hot`, `ex_cold`) → `df_hot_anom`, `df_cold_anom` (one row per year, `Perc_Anom` column).
   - Multiply by `3.6525` to express the percentage anomaly in **days/year** (≈ 365.25 / 100). Both representations should be available.
8. Figures (plotly, via `plot_timeseries_interactive`):
   - `F4_ST_hot_cold` — cold nights AND hot days percentage anomaly with trendlines.
   - `F4_ST_hot_cold_percentiles` — same with simple percentile counts (see step 9).
9. **Simple percentile counts** (second section of the notebook):
   - `q90 = st_data.loc['1961':'1991'].TMAX.quantile(0.9)`.
   - `q10 = st_data.loc['1961':'1991'].TMIN.quantile(0.1)`.
   - `st_max_counts` = annual count of `TMAX > q90`.
   - `st_min_counts` = annual count of `TMIN < q10`.
10. Persist results in `site_output_dir`:
    - `F4_ST_hot_cold_<site_tag>.png` + `.html`.
    - `F4_ST_hot_cold_percentiles_<site_tag>.png` + `.html`.
    - `T_hot_days_per_year_<site_tag>.csv` and `T_cold_nights_per_year_<site_tag>.csv`.
    - `T_hot_cold_summary_metrics_<site_tag>.json` with: `threshold_definition` (ETCCDI / fixed-percentile), `hot_days_per_year_stats`, `cold_nights_per_year_stats` (`n`, `mean`, `min`, `max`, `std`), `slope_hot_days`, `p_value_hot_days`, `slope_cold_nights`, `p_value_cold_nights`, `q90_TMAX_C`, `q10_TMIN_C`, `station_id`, `country`, `period`.

### Reporting style
- "At <station_id>, hot days exceed the day-of-year 90th percentile of 1961–1990. Annual count trend: S days/year (p = P)."
- "Cold nights are days with TMIN below the day-of-year 10th percentile of 1961–1990. Annual count trend: S days/year (p = P)."
- Always state which definition is in use (ETCCDI percentile-by-day vs simple fixed-percentile over 1961–1991).
- Color convention: hot days = warm tones (red/orange), cold nights = cool tones (blue).

### Hard rules
- Do NOT use percentile thresholds other than 90 (TMAX) / 10 (TMIN) in primary reporting unless explicitly requested.
- Do NOT change the base period (1961–1990) without explicit user request; it is hardcoded in `temp_func.py`.
- All figures must be produced via `plot_timeseries_interactive(...)` from `ind_setup.plotting_int`. If a new variant is needed, add it to `indicators_setup` first.
- The simple-percentile and ETCCDI variants must NOT be conflated in the same table; keep them in separate JSON sub-dictionaries.
