"""Generate the README figure for headwaters.

Live-downloads the source data for a single HUC12 and renders the three things
headwaters fetches — watershed boundary, DEM, and NHD flowlines — as one map.

Run:
    uv run --group example python examples/plot.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource

from headwaters.usgs_downloader import (
    download_wbd_boundary,
    download_nhd_flowlines,
    download_3dep_dem,
)

HUC = "180101080409"
CRS = "EPSG:3310"
DEM_RESOLUTION = 30
NHD_LAYER = "medium"

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def main() -> None:
    boundary = download_wbd_boundary(HUC)
    flowlines = download_nhd_flowlines(boundary, layer=NHD_LAYER, crs=CRS)
    dem = download_3dep_dem(boundary, DEM_RESOLUTION, CRS)

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
