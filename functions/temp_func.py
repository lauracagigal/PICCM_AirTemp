"""Temperature extremes helpers.

Implements the WMO/ETCCDI-style **hot-day** (``TX90p``) and **cold-night**
(``TN10p``) exceedance metrics used by the ``c_hot_cold_days`` notebook.

Two flavours are provided:

* :func:`exceedance_rate_for_base_period` — produces a yearly exceedance
  rate (one value per base-period year) using the 1961-1990 climatology.
* :func:`exceedance_rate_for_outbase_period` — returns the per-day
  threshold table for the 1961-1990 climatology so it can be applied to
  any other period (typically the full record).

Both rely on :func:`centered_percentile`, which estimates the 90th
percentile (for ``TMAX``) or the 10th percentile (for ``TMIN``) for each
calendar day using a centred 5-day window across all base-period years.
The base period is currently hardcoded to 1961-1990.
"""

from datetime import datetime

import numpy as np
import pandas as pd


# Base period for the percentile climatology (inclusive, calendar years).
BASE_PERIOD_START = 1961
BASE_PERIOD_END = 1990


def exceedance_rate_for_base_period(climate_data, variable_name):
    """Compute the yearly exceedance rate inside the base period.

    For each year in the base period (1961-1990), the function counts the
    fraction of days that exceed (for ``TMAX``) or fall below (for
    ``TMIN``) the day-specific percentile threshold derived from the same
    base period via :func:`centered_percentile`.

    Parameters
    ----------
    climate_data : pandas.DataFrame
        Daily climate data. Must contain at least the columns:

        - ``"DATE"``: ``datetime64[ns]`` timestamp per row.
        - ``"DAY"``: a ``datetime64[ns]`` "day-of-year" key shared across
          years (the notebooks construct it as
          ``"2024-" + DATE.strftime('%m-%d')``).
        - ``variable_name``: the temperature value in degrees Celsius.
    variable_name : {"TMAX", "TMIN"}
        Variable to evaluate. Determines the threshold direction
        (90th percentile / above for ``TMAX``; 10th percentile /
        below for ``TMIN``).

    Returns
    -------
    exceedance_rates : dict[int, float]
        Mapping ``year -> exceedance rate in [0, 1]``.
    all_exceedance_data : dict[int, dict[int, float]]
        Verbose variant of ``exceedance_rates`` retained for backward
        compatibility with older notebooks. Each entry is
        ``{year: {year: rate}}``.
    """
    exceedance_rates = {}
    all_exceedance_data = {}

    base_period_years = range(BASE_PERIOD_START, BASE_PERIOD_END + 1)
    base_period_data = climate_data[climate_data['DATE'].dt.year.isin(base_period_years)]

    # Precompute thresholds for all days in the base period
    thresholds = {}
    for day in base_period_data['DAY'].unique():
        thresholds[day] = centered_percentile(day, base_period_data, variable_name)

    for out_of_base_year in base_period_years:
        out_of_base_data = climate_data[climate_data['DATE'].dt.year == out_of_base_year].copy()
        out_of_base_data['THRESHOLD'] = out_of_base_data['DAY'].map(thresholds)

        if variable_name == "TMAX":
            exceedance_rate = (out_of_base_data[variable_name] > out_of_base_data['THRESHOLD']).mean()
        elif variable_name == "TMIN":
            exceedance_rate = (out_of_base_data[variable_name] < out_of_base_data['THRESHOLD']).mean()

        exceedance_rates[out_of_base_year] = exceedance_rate
        all_exceedance_data[out_of_base_year] = {out_of_base_year: exceedance_rate}

    return exceedance_rates, all_exceedance_data


def centered_percentile(date, base_df, variable_name):
    """Compute the day-of-year percentile threshold using a 5-day window.

    Pools all observations from the base period (1961-1990) that fall
    within ±2 days of every occurrence of the given calendar day, then
    returns the 90th percentile (for ``TMAX``) or 10th percentile (for
    ``TMIN``) of that pool. This matches the ETCCDI definition of the
    daily climatology used for ``TX90p`` / ``TN10p``.

    The base period is bracketed by ``1960-12-29`` and ``1991-01-02`` so
    that the 5-day window can extend across year boundaries without
    losing data on the first/last days of the year.

    Parameters
    ----------
    date : pandas.Timestamp or datetime-like
        Calendar day key (the ``"DAY"`` column of ``base_df``).
    base_df : pandas.DataFrame
        Daily data covering the base period. Must contain the columns
        ``"DATE"`` (actual timestamp), ``"DAY"`` (calendar-day key) and
        ``variable_name``.
    variable_name : {"TMAX", "TMIN"}
        Variable name; controls whether the 90th or 10th percentile is
        returned.

    Returns
    -------
    float
        Percentile threshold in the same units as ``variable_name``
        (degrees Celsius for ``TMIN``/``TMAX``).
    """
    filtered_df = base_df[(base_df["DATE"] >= datetime(1960, 12, 29)) & (base_df["DATE"] <= datetime(1991, 1, 2))]
    window_values = []

    for x in filtered_df[filtered_df['DAY'] == date]['DATE']:
        window_values.extend(filtered_df[(filtered_df['DATE'] >= x - pd.Timedelta(days=2)) &
                                         (filtered_df['DATE'] <= x + pd.Timedelta(days=2))][variable_name].tolist())

    if variable_name == "TMAX":
        return np.percentile(window_values, 90)
    elif variable_name == "TMIN":
        return np.percentile(window_values, 10)


def exceedance_rate_for_outbase_period(climate_data, variable_name):
    """Build the per-day percentile threshold table for one calendar year.

    Produces a 366-row DataFrame holding the day-of-year percentile
    derived from the base-period climatology (via
    :func:`centered_percentile`). This table can then be joined onto any
    period of interest — typically the full record — to count the number
    of hot days / cold nights for each year.

    The year 2024 is used purely as a leap-year placeholder so that
    February 29th is included.

    Parameters
    ----------
    climate_data : pandas.DataFrame
        Daily climate data spanning at least the base period. See
        :func:`exceedance_rate_for_base_period` for the expected schema.
    variable_name : {"TMAX", "TMIN"}
        Variable to evaluate.

    Returns
    -------
    pandas.DataFrame
        Columns: ``"DAY"`` (one row per calendar day of 2024) and
        ``"THRESHOLD"`` (percentile value to compare against).
    """
    date_range = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    df_exceedance = pd.DataFrame({'DAY': date_range})

    df_exceedance['THRESHOLD'] = df_exceedance['DAY'].apply(lambda day_value: centered_percentile(day_value, climate_data, variable_name))

    return df_exceedance
