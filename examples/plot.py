"""Generate the README figure for headwaters.

Live-downloads the source data for a single HUC12 with fetch_huc and renders the
DEM (hillshaded) with the NHD flowlines on top. Flowlines whose upstream end sits
on the watershed boundary are dropped — a real headwater starts inside the basin,
so a start-on-boundary reach is a clip artifact that otherwise seeds a spurious
channel head (and a bogus secondary network) downstream in catchment.

Run:
    uv run --group example python examples/plot.py
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource
from shapely.geometry import Point

from headwaters import fetch_huc
from headwaters.usgs_downloader import download_wbd_boundary

HUC = "180101080409"
CRS = "EPSG:3310"
DEM_RESOLUTION = 30
NHD_LAYER = "medium"
BOUNDARY_START_BUFFER = 20  # metres; drop reaches whose head is on the boundary

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def drop_boundary_heads(flowlines: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame):
    """Drop flowlines whose upstream endpoint lies within
    BOUNDARY_START_BUFFER metres of the watershed boundary."""
    bline = boundary.union_all().boundary
    starts = gpd.GeoSeries(
        [Point(g.coords[0]) for g in flowlines.geometry],
        crs=flowlines.crs,
        index=flowlines.index,
    )
    return flowlines[starts.distance(bline) >= BOUNDARY_START_BUFFER]


def main() -> None:
    dem, flowlines = fetch_huc(
        HUC, nhd_layer=NHD_LAYER, dem_resolution=DEM_RESOLUTION, crs=CRS
    )
    boundary = download_wbd_boundary(HUC).to_crs(CRS)
    flowlines = drop_boundary_heads(flowlines, boundary)

    z = dem.values.astype(float)
    z = np.where(np.isfinite(z), z, np.nan)
    left, right = float(dem.x.min()), float(dem.x.max())
    bottom, top = float(dem.y.min()), float(dem.y.max())
    extent = (left, right, bottom, top)

    ls = LightSource(azdeg=315, altdeg=45)
    hillshade = ls.hillshade(z, vert_exag=2, dx=DEM_RESOLUTION, dy=DEM_RESOLUTION)

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.imshow(hillshade, cmap="gray", extent=extent, origin="upper")
    im = ax.imshow(z, cmap="terrain", extent=extent, origin="upper", alpha=0.55)
    flowlines.plot(ax=ax, color="black", linewidth=1.5)

    ax.set_xlim(left, right)
    ax.set_ylim(bottom, top)
    ax.set_axis_off()
    ax.set_title(
        f"HUC {HUC}  ·  DEM ({DEM_RESOLUTION} m) + NHD flowlines ({NHD_LAYER} resolution)",
        fontsize=11,
    )
    cbar = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("elevation (m)", fontsize=9)

    ASSETS.mkdir(exist_ok=True)
    out = ASSETS / "headwaters.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
