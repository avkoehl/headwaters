# headwaters

Given a HUC ID, produce a DEM, flowlines, conditioned DEM, flow directions, and
flow accumulation. Thin wrapper around pygeohydro/pynhd/py3dep (data download)
and whitebox/pysheds (DEM conditioning, flow direction, flow accumulation).

```python
from headwaters import get_headwaters

dem, flowlines, conditioned_dem, flow_dir, flow_acc = get_headwaters("1805000203")
```
