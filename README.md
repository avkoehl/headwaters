# headwaters

Fetch source data for a watershed from USGS services: the boundary, DEM, and
NHD flowlines for a given HUC ID. Thin wrapper around the HyRiver stack
(pygeohydro/pynhd/py3dep) — no terrain computation, no compiled dependencies.

```python
from headwaters import fetch_huc

dem, flowlines = fetch_huc("1805000203", crs="EPSG:3310")
```
