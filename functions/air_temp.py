"""Shared helpers for PICCM Air Temperature notebooks.

This module is the air-temperature counterpart of ``sea_level.py`` in the
``PICCM_SeaLevel`` repository. It centralises **site configuration handling**
so that every historical notebook (``a_mean_temperature``,
``b_min_max_temperature``, ``c_hot_cold_days``) can be parameterised from a
single ``00_site_setup`` notebook.

The site configuration is a plain dictionary persisted as JSON in
``data/sites/<site>.json``. Typical keys include:

- ``site_name`` (str): Human-readable site name (e.g. ``"Palau"``).
- ``site_lon`` / ``site_lat`` (float): Site coordinates in decimal degrees.
- ``country`` (str): Country name used by the GHCN downloader.
- ``ghcn_station_id`` (str): GHCN-Daily station identifier (e.g. ``"PSW00040309"``).
- ``ghcn_station_name`` (str, optional): Human-readable station name.
- ``vars_interest`` (list[str]): Variables to fetch (e.g. ``["TMIN", "TMAX"]``).
- ``reference_period_start`` / ``reference_period_end`` (str): Climatology window
  bounds (years as 4-character strings, used for pandas label-based slicing).
- ``completeness_threshold`` (float): Minimum fraction of valid days/months
  required to keep a period.
"""

from pathlib import Path

import numpy as np
import pandas as pd


def haversine_km(lon1, lat1, lon2, lat2):
    """Great-circle distance in kilometres between two points.

    Vectorised over the inputs: each argument may be a scalar or a
    numpy array, and the standard broadcasting rules apply. Coordinates
    are in decimal degrees.

    Used in ``00_site_setup`` to rank GHCN-Daily stations by distance to
    the user's site coordinates.

    Parameters
    ----------
    lon1, lat1 : float or array-like
        Longitude and latitude of the first point(s) in decimal degrees.
    lon2, lat2 : float or array-like
        Longitude and latitude of the second point(s) in decimal degrees.

    Returns
    -------
    float or numpy.ndarray
        Great-circle distance in kilometres. The output shape follows
        numpy broadcasting between the inputs.
    """
    r = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def save_site_config(config_dict, output_path):
    """Persist a site-configuration dictionary as a JSON file.

    The parent directory of ``output_path`` is created if it does not exist.
    The dictionary is serialised through :class:`pandas.Series` so non-ASCII
    characters in site names (e.g. accented letters) are preserved.

    Parameters
    ----------
    config_dict : dict
        Site configuration. Keys are stored verbatim. See the module
        docstring for the conventional schema.
    output_path : str or pathlib.Path
        Destination JSON file (e.g. ``"../../data/sites/palau.json"``).

    Returns
    -------
    pathlib.Path
        Resolved path of the file that was written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.Series(config_dict).to_json(output_path, indent=2, force_ascii=False)
    return output_path


def load_site_config(config_path):
    """Load a site-configuration dictionary previously written with
    :func:`save_site_config`.

    Parameters
    ----------
    config_path : str or pathlib.Path
        Path to the JSON site-config file.

    Returns
    -------
    dict
        Site configuration mapping. Values keep the JSON-native types
        (``str``, ``int``, ``float``, ``list``, ``None``).

    Raises
    ------
    FileNotFoundError
        If ``config_path`` does not exist. The site-setup notebook
        (``00_site_setup.ipynb``) must be executed at least once before
        any other historical notebook can be run.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Site config not found: {config_path}")
    return pd.read_json(config_path, typ="series").to_dict()


def build_site_tag(site_name, site_lon, site_lat):
    """Build a filename-safe identifier that uniquely tags a site.

    The tag combines a slugified version of ``site_name`` with both
    coordinates so that exported figures and tables for different sites
    never overwrite each other. Coordinates are formatted with three
    decimals; ``.`` is replaced by ``p`` and the negative sign by ``m`` to
    keep the result safe on every filesystem.

    Examples
    --------
    >>> build_site_tag("Palau", 134.620, 7.340)
    'palau_lat7p340_lon134p620'
    >>> build_site_tag("American Samoa", -170.7, -14.3)
    'american_samoa_latm14p300_lonm170p700'

    Parameters
    ----------
    site_name : str
        Human-readable site name. Non-alphanumeric characters are
        replaced with underscores and the result is lowercased.
    site_lon, site_lat : float
        Site coordinates in decimal degrees.

    Returns
    -------
    str
        Filesystem-safe site tag.
    """
    safe_name = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(site_name)).strip("_")
    safe_name = "_".join(part for part in safe_name.split("_") if part)
    lat_str = f"{float(site_lat):.3f}".replace(".", "p").replace("-", "m")
    lon_str = f"{float(site_lon):.3f}".replace(".", "p").replace("-", "m")
    return f"{safe_name}_lat{lat_str}_lon{lon_str}"


def build_output_filename(base_name, site_name, site_lon, site_lat, ext="png"):
    """Build a standardised output filename of the form
    ``"<base_name>_<site_tag>.<ext>"``.

    Useful for figures and tables that need to live in a shared output
    directory but stay disambiguated per site.

    Parameters
    ----------
    base_name : str
        Plot/table identifier (e.g. ``"F2_ST_Annomalies_top10"``).
    site_name : str
        Site name forwarded to :func:`build_site_tag`.
    site_lon, site_lat : float
        Site coordinates forwarded to :func:`build_site_tag`.
    ext : str, optional
        File extension. Leading dots are stripped. Defaults to ``"png"``.

    Returns
    -------
    str
        Composed filename (no directory component).
    """
    site_tag = build_site_tag(site_name, site_lon, site_lat)
    ext = ext.lstrip(".")
    return f"{base_name}_{site_tag}.{ext}"
