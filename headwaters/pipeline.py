import geopandas as gpd
import xarray as xr

from .usgs_downloader import download_huc_data
from .accumulation import flow_accumulation_workflow


def get_headwaters(
    hucid: str,
    nhd_layer: str = "medium",
    crs: str = "EPSG:4326",
    dem_resolution: int = 10,
) -> tuple[xr.DataArray, gpd.GeoDataFrame, xr.DataArray, xr.DataArray, xr.DataArray]:
    """Given a HUC ID, download the DEM and flowlines and derive flow direction
    and flow accumulation.

    Args:
        hucid: The Hydrologic Unit Code identifier for the watershed area.
        nhd_layer: Options: "medium" for medium resolution or "high" for high resolution.
        crs: The coordinate reference system for the output data as an EPSG code
            or other CRS string. Defaults to "EPSG:4326" (WGS84).
        dem_resolution: The spatial resolution of the DEM in meters. Defaults to 10.

    Returns:
        (dem, flowlines, conditioned_dem, flow_dir, flow_acc)
    """
    dem, flowlines = download_huc_data(
        hucid, nhd_layer=nhd_layer, crs=crs, dem_resolution=dem_resolution
    )
    conditioned_dem, flow_dir, flow_acc = flow_accumulation_workflow(dem)
    return dem, flowlines, conditioned_dem, flow_dir, flow_acc
