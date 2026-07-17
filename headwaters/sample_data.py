from platformdirs import user_cache_dir
from pathlib import Path
import rioxarray
import geopandas as gpd
import xarray as xr

from .usgs_downloader import fetch_huc

CACHE_DIR = Path(user_cache_dir("headwaters"))


def load_sample_data() -> tuple[xr.DataArray, gpd.GeoDataFrame]:
    """
    Load sample DEM and flowline data for a specific HUC ID. If the data is
    not already cached, it will be downloaded and saved to the cache
    directory for future use.

    Returns:
       A tuple containing the DEM as an xarray DataArray and the flowlines as a GeoDataFrame.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dem_path = CACHE_DIR / "sample_dem.tif"
    flowlines_path = CACHE_DIR / "sample_flowlines.gpkg"

    if not dem_path.exists() or not flowlines_path.exists():
        print(f"Sample data not found in cache. Downloading to {CACHE_DIR}...")
        dem, flowlines = fetch_huc("1805000203", crs="EPSG:3310")
        dem.rio.to_raster(dem_path)
        flowlines.to_file(flowlines_path, driver="GPKG")
    else:
        print(f"Loading sample data from cache at {CACHE_DIR}...")

    dem = rioxarray.open_rasterio(dem_path).squeeze()
    flowlines = gpd.read_file(flowlines_path)
    return (dem, flowlines)
