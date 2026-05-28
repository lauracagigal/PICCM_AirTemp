"""Public-data downloaders for the PICCM Air Temperature indicators.

This module groups thin wrappers around the public endpoints that the
historical notebooks rely on. Every helper here is a *pure* downloader:
it fetches the remote payload, normalises it into a pandas/xarray object
and returns it without writing to disk (with the exception of
:func:`download_uhslc_data`, which caches the NetCDF file locally).

Data sources
------------
- **MLO CO2** — Mauna Loa monthly CO2 from NOAA GML.
- **HOT CO2 / pH** — Hawaii Ocean Time-series surface CO2/pH.
- **GHCN-Daily** — Global Historical Climatology Network (NOAA NCEI),
  exposed as the :class:`GHCN` namespace.
- **IBTrACS** — International Best Track Archive for Climate Stewardship.
- **ONI** — Oceanic Niño Index from NOAA PSL.
- **ERDDAP** — Generic ERDDAP gridded download.
- **UHSLC** — University of Hawaii Sea Level Center tide-gauge data.

A standalone utility, :func:`filter_by_time_completeness`, is also
provided to drop months/years that do not meet a configurable data
completeness threshold.
"""

import os
import os.path as op
from io import BytesIO, StringIO
from urllib.request import urlretrieve

import numpy as np
import pandas as pd
import requests
import xarray as xr


# ---------------------------------------------------------------------------
# Mauna Loa CO2
# ---------------------------------------------------------------------------
def download_MLO_CO2_data(url):
    """Download monthly mean CO2 measurements from Mauna Loa Observatory.

    Reads the NOAA GML text file at ``url`` and returns it as a tidy
    monthly time series. The graphs reflect direct atmospheric CO2
    measurements started by C. D. Keeling (Scripps) in March 1958 at
    Mauna Loa, Hawaii.

    Suggested URL
    -------------
    ``https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.txt``

    Parameters
    ----------
    url : str
        URL of the NOAA GML monthly file.

    Returns
    -------
    pandas.DataFrame
        Single-column DataFrame with monthly CO2 (column ``"CO2"``)
        indexed by ``DatetimeIndex`` set to the first day of each month.
        Missing values are coded as NaN.
    """
    MLO_data = pd.read_csv(
        url,
        skiprows=42,
        sep=r'\s+',
        header=None,
        usecols=[0, 1, 3],
        names=['year', 'month', 'CO2'],
        na_values=-99.99,
    )
    MLO_data.index = pd.to_datetime(MLO_data[['year', 'month']].assign(day=1))
    MLO_data = MLO_data.drop(columns=['year', 'month'])

    return MLO_data


# ---------------------------------------------------------------------------
# Hawaii Ocean Time-series (HOT)
# ---------------------------------------------------------------------------
def download_HOT_CO2_data(url: str) -> pd.DataFrame:
    """Download surface CO2 and pH measurements from the HOT program.

    Reads the whitespace-separated ASCII file shipped by the HOT program
    (U. Hawaii) at ``url`` and returns it as a daily time series of
    in-situ ``pCO2`` (renamed to ``CO2``) and pH.

    Suggested URL
    -------------
    ``http://hahana.soest.hawaii.edu/hotco2/HOT_surface_CO2.txt``

    Reference
    ---------
    Dore, J.E., R. Lukas, D.W. Sadler, M.J. Church, and D.M. Karl. 2009.
    Physical and biogeochemical modulation of ocean acidification in the
    central North Pacific. *Proc Natl Acad Sci USA* 106: 12235-12240.

    Parameters
    ----------
    url : str
        URL of the HOT surface CO2 text file.

    Returns
    -------
    pandas.DataFrame
        DataFrame with two columns, ``"CO2"`` (``pCO2calc_insitu``) and
        ``"pH"`` (``pHmeas_insitu``), indexed by the sample date.
        Sentinel value ``-999.0`` is converted to NaN.
    """
    HOT_data = pd.read_csv(url, header=7, sep=r'\s+', na_values=-999.0)
    HOT_data.index = pd.to_datetime(HOT_data['date'], format='%d-%b-%y')
    HOT_data = HOT_data.drop(columns=['date']).rename(
        columns={'pCO2calc_insitu': 'CO2', 'pHmeas_insitu': 'pH'}
    )

    return HOT_data


# ---------------------------------------------------------------------------
# GHCN — Global Historical Climatology Network (Daily)
# ---------------------------------------------------------------------------
class GHCN:
    """Namespace for GHCN-Daily download helpers (NOAA NCEI).

    The Global Historical Climatology Network-Daily database is a
    composite of climate records from numerous sources merged and
    subjected to a suite of quality-assurance reviews. The archive
    includes 40+ meteorological elements (temperature daily
    maximum/minimum, temperature at observation time, precipitation,
    snow, etc.).

    Reference
    ---------
    https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/
    """

    @staticmethod
    def download_country_codes():
        """Download the GHCN country-code lookup table.

        Returns
        -------
        pandas.DataFrame
            DataFrame with two columns:

            - ``"Code"`` (str): Two-letter GHCN country code.
            - ``"Country"`` (str): Country name.
        """
        url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-countries.txt"

        country_codes = requests.get(url).text
        country_codes = country_codes.split("\n")

        codes = [line.split(" ")[0] for line in country_codes]
        countries = [
            " ".join(line.split(" ")[1:]).strip() for line in country_codes
        ]

        df_countries = pd.DataFrame({"Code": codes, "Country": countries})

        return df_countries

    @staticmethod
    def get_country_code(country):
        """Look up the GHCN country code for a given country name.

        Parameters
        ----------
        country : str
            Country name as it appears in the GHCN country file
            (e.g. ``"Palau"``).

        Returns
        -------
        pandas.DataFrame
            One-row (or zero-row) DataFrame with columns ``"Code"`` and
            ``"Country"`` corresponding to ``country``.
        """
        df = GHCN.download_country_codes()

        return df.loc[df["Country"] == country]

    @staticmethod
    def download_stations_info():
        """Download metadata for every GHCN-Daily station.

        Returns
        -------
        pandas.DataFrame
            DataFrame with one row per station and columns:

            - ``"ID"`` (str): Station identifier (the country code is the
              first two characters).
            - ``"Latitude"`` (float): Latitude in decimal degrees.
            - ``"Longitude"`` (float): Longitude in decimal degrees.
            - ``"Elevation"`` (float): Elevation in metres.
            - ``"Name"`` (str): Station name.
        """
        url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"

        stations = requests.get(url).text
        stations = stations.split("\n")

        processed_data = []
        for line in stations:
            if len(line) > 0:
                parts = line.split()
                station_id = parts[0]
                latitude = float(parts[1])
                longitude = float(parts[2])
                elevation = float(parts[3])
                name = " ".join(parts[4:])
                processed_data.append([station_id, latitude, longitude, elevation, name])

        df_stations = pd.DataFrame(
            processed_data, columns=["ID", "Latitude", "Longitude", "Elevation", "Name"]
        )

        return df_stations

    @staticmethod
    def extract_dict_data_var(GHCND_dir, var, df_country_stations):
        """Download per-station time series for a single GHCN variable.

        Iterates over every station in ``df_country_stations`` and, when
        the station file contains ``var``, downloads the CSV, divides
        temperature/precipitation values by 10 (GHCN stores them in
        tenths of degrees Celsius / tenths of millimetres) and packages
        the result in a dictionary suitable for the plotting helpers in
        ``indicators_setup``.

        Side effects
        ------------
        Creates a global variable ``dict_<var>`` mirroring the returned
        list. Kept for backward compatibility with notebooks that
        reference it directly; new code should rely on the return value.

        Parameters
        ----------
        GHCND_dir : str
            Base URL of the GHCND CSV archive, typically
            ``"https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/"``.
        var : str
            GHCN variable to extract (``"TMIN"``, ``"TMAX"``, ``"PRCP"``,
            ``"TAVG"``, ...). For ``TMIN``/``TMAX``/``PRCP`` the values
            are divided by 10 before being returned.
        df_country_stations : pandas.DataFrame
            Subset of :meth:`download_stations_info` with the candidate
            stations. Must contain at least the columns ``"ID"`` and
            ``"Name"``.

        Returns
        -------
        records : list[dict]
            One dictionary per station that actually contains ``var``:

            - ``"data"``: ``pandas.DataFrame`` with a single column
              named ``var`` indexed by ``DATE``.
            - ``"var"``: ``str`` — equal to ``var``.
            - ``"ax"``: ``int`` — plotting axis hint (always ``1``).
            - ``"label"``: ``str`` — ``"Station <ID>"``.
        IDS : list[str]
            Station identifiers, in the same order as ``records``.
        """
        dict_name = f"dict_{var}"
        globals()[dict_name] = []
        IDS = []
        for i in range(len(df_country_stations)):

            url_download = GHCND_dir + df_country_stations.iloc[i]['ID'] + '.csv'

            df = pd.read_csv(url_download, na_values=['-9999'])
            df.index = pd.to_datetime(df['DATE'])

            if var in df.columns:

                IDS.append(df_country_stations.iloc[i]['ID'])

                if var == 'TMIN' or var == 'TMAX' or var == 'PRCP':
                    df[var] = df[var] / 10
                    label = f"Station {df_country_stations.iloc[i]['ID']}"
                else:
                    label = f"Station {df_country_stations.iloc[i]['ID']}"

                info_dic = {'data': df[[var]], 'var': var, 'ax': 1, 'label': label}
                globals()[dict_name].append(info_dic)

        return globals()[dict_name], IDS


# ---------------------------------------------------------------------------
# IBTrACS — tropical cyclone best tracks
# ---------------------------------------------------------------------------
def download_ibtracs(url, basin=None):
    """Download the IBTrACS NetCDF best-track archive.

    The full dataset is downloaded into memory and opened with xarray.
    Optionally restricted to a single basin.

    Parameters
    ----------
    url : str
        URL of an IBTrACS NetCDF file (e.g. one of the
        ``IBTrACS.ALL.v04r00.nc`` or per-basin files at NCEI).
    basin : str, optional
        Basin code to filter on (e.g. ``"WP"`` for Western Pacific,
        ``"EP"``, ``"NA"``, ``"SI"``, ``"SP"``, ``"NI"``). The filter
        compares against the basin assignment at the first time step of
        each storm. If ``None`` (default), all storms are returned.

    Returns
    -------
    xarray.Dataset
        Subset containing the variables ``wmo_wind``, ``wmo_pres`` and
        ``name``. Returns the full dataset object even if the HTTP
        request failed (in which case ``tcs`` is unset and an error
        message is printed).
    """
    response = requests.get(url)
    if response.status_code == 200:
        tcs = xr.open_dataset(BytesIO(response.content))
    else:
        print(f"Error while downloading file: {response.status_code}")

    if basin:
        tcs = tcs.isel(storm=np.where(tcs.isel(date_time=0).basin.values.astype(str) == basin)[0])

    return tcs[['wmo_wind', 'wmo_pres', 'name']]


# ---------------------------------------------------------------------------
# ONI — Oceanic Niño Index
# ---------------------------------------------------------------------------
def download_oni_index(p_data):
    """Download the Oceanic Niño Index (ONI) and reshape it to monthly.

    The ONI is the standard measure for monitoring El Niño / La Niña
    events: a 3-month running mean of sea-surface-temperature anomalies
    in the Niño 3.4 region. The text file at NOAA PSL is laid out as one
    row per year with twelve monthly columns; this helper flattens it
    into a single column indexed by month.

    Suggested URL
    -------------
    ``https://psl.noaa.gov/data/correlation/oni.data``

    Reference
    ---------
    https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php

    Parameters
    ----------
    p_data : str
        URL (or local path) of the ONI ASCII file.

    Returns
    -------
    pandas.DataFrame
        Single-column (``"ONI"``) DataFrame indexed monthly. The
        sentinel value ``-99.9`` is converted to NaN.
    """
    content = requests.get(p_data).content.decode()
    oni = pd.read_csv(
        StringIO(content), skiprows=1, sep=r'\s+', header=None, index_col=0
    )[1:-8]
    oni = oni.apply(pd.to_numeric, errors="coerce")

    df1 = pd.DataFrame(oni.values.reshape(-1), columns=["ONI"])
    df1.index = pd.date_range(
        start=f"{oni.index[0]}-01-01", periods=len(df1), freq="MS"
    )
    df1.replace(-99.9, np.nan, inplace=True)

    return df1


# ---------------------------------------------------------------------------
# ERDDAP
# ---------------------------------------------------------------------------
def download_ERDDAP_data(base_url, dataset_id, date_ini, date_end, lon_range, lat_range):
    """Download a gridded variable subset from an ERDDAP server.

    Builds the ERDDAP ``griddap`` query that selects a temporal slice
    between ``date_ini`` and ``date_end`` and the bounding box defined
    by ``lon_range`` × ``lat_range``, then loads the CSV response into a
    DataFrame. The numeric columns are coerced to floats.

    Notes
    -----
    The first data row of an ERDDAP CSV holds the units rather than data,
    so it is skipped via ``.iloc[1:]``.

    Parameters
    ----------
    base_url : str
        ERDDAP endpoint URL (must end with the dataset's ``.csv`` path).
    dataset_id : str
        Variable identifier to request from the dataset.
    date_ini, date_end : str
        ISO-8601 start/end timestamps (e.g. ``"2020-01-01"``).
    lon_range, lat_range : tuple of float
        ``(min, max)`` bounding box in decimal degrees.

    Returns
    -------
    pandas.DataFrame
        Columns include ``"time"`` (datetime), ``"latitude"``,
        ``"longitude"`` and ``dataset_id`` (all floats).
    """
    url = f'{base_url}?{dataset_id}%5B({date_ini}):1:({date_end})%5D%5B({lat_range[0]}):1:({lat_range[1]})%5D%5B({lon_range[0]}):1:({lon_range[1]})%5D'
    data = pd.read_csv(url).iloc[1:].reset_index(drop=True)
    data['time'] = pd.to_datetime(data['time'].values)
    for var in ['latitude', 'longitude', dataset_id]:
        data[var] = data[var].astype(float)
    return data


# ---------------------------------------------------------------------------
# UHSLC — University of Hawaii Sea Level Center
# ---------------------------------------------------------------------------
def download_uhslc_data(data_dir: str, uhslc_id: int, frequency: str = 'hourly'):
    """Download a UHSLC tide-gauge NetCDF and cache it on disk.

    The file is first downloaded to a temporary name to avoid corrupting
    an existing cached copy on failure, and only renamed into place on
    success. ``record_id`` is divided by 10 (UHSLC appends a trailing
    zero for uniqueness) and ``station_name`` / ``station_country`` are
    coerced to native Python strings.

    Endpoints
    ---------
    - Hourly:  ``https://uhslc.soest.hawaii.edu/data/netcdf/fast/hourly/``
    - Daily:   ``https://uhslc.soest.hawaii.edu/data/netcdf/fast/daily/``

    Parameters
    ----------
    data_dir : str or pathlib.Path
        Directory where the NetCDF file is cached.
    uhslc_id : int
        UHSLC station identifier (e.g. ``7`` for Malakal, Palau).
    frequency : {"hourly", "daily"}, optional
        Sampling frequency to download. Defaults to ``"hourly"``.

    Returns
    -------
    xarray.Dataset
        The opened tide-gauge dataset. The file remains on disk at
        ``<data_dir>/{h|d}<uhslc_id:03>.nc`` for reuse.
    """
    fname = f'{frequency[0]}{uhslc_id:03}.nc'  # h for hourly, d for daily

    if frequency == 'hourly':
        url = "https://uhslc.soest.hawaii.edu/data/netcdf/fast/hourly/"
    elif frequency == 'daily':
        url = "https://uhslc.soest.hawaii.edu/data/netcdf/fast/daily/"

    path = os.path.join(data_dir, fname)
    temp_path = os.path.join(data_dir, 'temp_' + fname)
    urlretrieve(os.path.join(url, fname), temp_path)

    if os.path.exists(path):
        # Avoid a permission error from the file being open: remove the
        # old cached copy before promoting the freshly downloaded one.
        os.remove(path)

    os.rename(temp_path, path)

    rsl = xr.open_dataset(path, engine="h5netcdf")

    # The trailing zero on record_id is appended by UHSLC to make the
    # identifier unique when a station has multiple entries.
    rsl['record_id'] = (rsl['record_id'] / 10).astype(int)

    for col in ['station_name', 'station_country']:
        rsl[col] = rsl[col].astype(str)

    return rsl


# ---------------------------------------------------------------------------
# Time-completeness filter
# ---------------------------------------------------------------------------
def filter_by_time_completeness(
    df,
    time_col="time",
    month_threshold=0.75,
    year_threshold=0.75,
):
    """Drop months and years with too few observations.

    A two-stage filter:

    1. **Month level** — a month is kept if its number of distinct days
       with observations is at least ``month_threshold`` of the
       calendar-month length (e.g. 23 out of 31).
    2. **Year level** — a year is kept if at least ``year_threshold`` of
       its observed months passed the month-level test.

    The filter operates on the DataFrame's ``DatetimeIndex`` (the
    ``time_col`` argument is accepted for backwards compatibility but is
    not used internally). Helper columns ``year``/``month``/``day`` are
    added during processing and dropped before returning.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame with daily data; must be indexed (or
        index-convertible) by a ``DatetimeIndex``.
    time_col : str, optional
        Retained for API compatibility (ignored).
    month_threshold : float, optional
        Minimum fraction of days required to keep a month
        (default ``0.75``).
    year_threshold : float, optional
        Minimum fraction of valid months required to keep a year
        (default ``0.75``).

    Returns
    -------
    df_filtered : pandas.DataFrame
        Copy of ``df`` restricted to the months/years that pass both
        thresholds, without the helper ``year``/``month``/``day``
        columns.
    removed_months : pandas.DataFrame
        Months that failed the month-level test. Indexed by
        ``(year, month)`` with a single column ``month_completeness``.
    removed_years : pandas.Series
        Years that failed the year-level test, indexed by year, with
        the year-completeness ratio as values.
    """
    df = df.copy()

    df.index = pd.to_datetime(df.index)
    df["year"] = df.index.year
    df["month"] = df.index.month
    df["day"] = df.index.day

    days_present = (
        df.groupby(["year", "month"])["day"]
        .nunique()
        .rename("days_present")
    )

    days_in_month = (
        days_present
        .reset_index()
        .assign(
            days_in_month=lambda x: pd.to_datetime(
                dict(year=x.year, month=x.month, day=1)
            ).dt.days_in_month
        )
        .set_index(["year", "month"])["days_in_month"]
    )

    month_completeness = days_present / days_in_month

    valid_months = month_completeness >= month_threshold

    removed_months = (
        month_completeness[~valid_months]
        .to_frame(name="month_completeness")
    )

    valid_months_per_year = valid_months.groupby("year").sum()
    total_months_per_year = df.groupby("year")["month"].nunique()

    year_completeness = valid_months_per_year / total_months_per_year

    valid_years = year_completeness >= year_threshold

    removed_years = year_completeness[~valid_years]

    df_filtered = df[
        df.set_index(["year", "month"]).index.isin(
            valid_months[valid_months].index
        )
    ]

    df_filtered = df_filtered[
        df_filtered["year"].isin(valid_years[valid_years].index)
    ]

    df_filtered = df_filtered.drop(columns=["year", "month", "day"])

    return df_filtered, removed_months, removed_years
