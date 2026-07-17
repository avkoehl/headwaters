"""
Uses pygeohydro methods to get the watershed boundary, flowlines, and DEM for a given HUC ID
"""

import warnings

import geopandas as gpd
import pandas as pd
import py3dep
import rasterio
from pygeohydro import WBD
from pynhd import NHD, NHDPlusHR
from rioxarray.merge import merge_arrays
from shapely.geometry import Polygon, MultiPolygon
import xarray as xr


def fetch_huc(
    hucid: str,
    nhd_layer: str = "medium",
    crs: str = "EPSG:4326",
    dem_resolution: int = 10,
) -> tuple[xr.DataArray, gpd.GeoDataFrame]:
    """Download hydrological and topographic data for a given HUC ID.

    Calls download_wbd_boundary, download_nhd_flowlines, and download_3dep_dem,
    returning the dem and flowlines clipped to the watershed boundary.


    Args:
        hucid: The Hydrologic Unit Code identifier for the watershed area.
        nhd_layer: Options: "medium" for medium resolution or "high" for high resolution.
        crs: The coordinate reference system for the output data as an EPSG code
            or other CRS string. Defaults to "EPSG:4326" (WGS84).
        dem_resolution: The spatial resolution of the DEM in meters. Defaults to 10.

    Returns:
    (dem, flowlines): A tuple containing the watershed boundary as a GeoDataFrame.

    """
    huc_bounds = download_wbd_boundary(hucid)
    flowlines = download_nhd_flowlines(
        huc_bounds, layer=nhd_layer, linestring_only=True, crs=crs
    )
    dem = download_3dep_dem(huc_bounds, dem_resolution, crs)

    return (dem, flowlines)


def download_nhd_flowlines(
    area: gpd.GeoDataFrame | Polygon | MultiPolygon,
    layer: str = "medium",
    linestring_only: bool = True,
    crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """Download NHD flowlines for a given area.

    Args:
        area: Area of interst as a GeoDataFrame, Polygon, or MultiPolygon.
        layer: Options: "medium" for medium resolution or "high" for high resolution.
        linestring_only: If True, only return LineString geometries. Defaults to True.
        crs: The coordinate reference system for the output data as an EPSG code. Defaults to "EPSG:4326" (WGS84).

    Returns:
        Flowlines as a GeoDataFrame clipped to the input area and reprojected to the specified CRS.
    """

    if isinstance(area, gpd.GeoDataFrame):
        gdf = area
    else:
        gdf = gpd.GeoDataFrame(geometry=[area], crs=crs)

    boundary = gdf.union_all()
    bbox = boundary.bounds

    if layer == "medium":
        flowlines = NHD("flowline_mr").bygeom(bbox)
        flowlines.columns = flowlines.columns.str.lower()
    elif layer == "high":
        flowlines = NHDPlusHR("flowline").bygeom(bbox)
        flowlines.columns = flowlines.columns.str.lower()
        try:
            non_network = NHDPlusHR("non_network_flowline").bygeom(bbox)
            non_network.columns = non_network.columns.str.lower()
            flowlines = gpd.GeoDataFrame(
                pd.concat([flowlines, non_network], ignore_index=True), crs=gdf.crs
            )
        except Exception:
            pass
    else:
        raise ValueError("layer must be 'medium' or 'high'")

    if "fcode" in flowlines.columns:
        flowlines = flowlines[~flowlines.fcode.isin([566, 56600])]  # exclude coastlines

    flowlines = flowlines.clip(gdf.geometry, gdf.crs).explode()

    if linestring_only:
        flowlines = flowlines[flowlines.geometry.type == "LineString"]

    return flowlines.to_crs(crs)


def download_3dep_dem(
    area: gpd.GeoDataFrame | Polygon | MultiPolygon,
    resolution: int = 10,
    crs: str = "EPSG:4326",
) -> xr.DataArray:
    """Download a 3DEP DEM for a given area.

    Attempts a single request first. If that fails (e.g. area too large), retries
    by splitting the bounding box into four quadrants and mosaicking the results.

    Args:
        area: Area of interest as a GeoDataFrame, Polygon, or MultiPolygon.
        resolution: DEM resolution in meters. Defaults to 10.
        crs: Output CRS. Defaults to "EPSG:4326".

    Returns:
        DEM as an xarray DataArray.
    """
    if isinstance(area, gpd.GeoDataFrame):
        gdf = area
    else:
        gdf = gpd.GeoDataFrame(geometry=[area], crs=crs)

    boundary = gdf.union_all()
    bbox = boundary.bounds  # (minx, miny, maxx, maxy)

    try:
        dem = py3dep.static_3dep_dem(bbox, resolution=resolution, crs=gdf.crs)
    except Exception as e:
        warnings.warn(
            f"DEM download failed ({e}). Retrying using tiled downloads — "
            "the query area may be too large for a single request."
        )
        minx, miny, maxx, maxy = bbox
        mid_x = (minx + maxx) / 2
        mid_y = (miny + maxy) / 2

        quadrants = [
            (minx, miny, mid_x, mid_y),  # bottom-left
            (mid_x, miny, maxx, mid_y),  # bottom-right
            (minx, mid_y, mid_x, maxy),  # top-left
            (mid_x, mid_y, maxx, maxy),  # top-right
        ]
        tiles = [
            py3dep.get_dem(q, crs=gdf.crs, resolution=resolution) for q in quadrants
        ]
        dem = merge_arrays(tiles)

    dem = dem.rio.clip(gdf.geometry.tolist(), gdf.crs, drop=True, all_touched=True)

    if dem.rio.crs != crs:
        dem = dem.rio.reproject(crs, resampling=rasterio.enums.Resampling.bilinear)

    return dem


def download_wbd_boundary(huc: str) -> gpd.GeoDataFrame:
    """Download the WBD watershed boundary for a given HUC ID.

    Args:
        huc: HUC ID as a string or integer. Level is inferred from the length of the ID.

    Returns:
        Watershed boundary as a GeoDataFrame.
    """
    huc = str(huc)
    level = f"huc{str(len(huc))}"
    wbd = WBD(level)

    huc_wbd = wbd.byids(level, huc)
    return huc_wbd
