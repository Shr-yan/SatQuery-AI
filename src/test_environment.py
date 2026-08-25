import rasterio
import numpy as np
import pyproj
import shapely
from PIL import Image

print("=== SatQuery AI Phase 1 Environment ===")
print("Rasterio:", rasterio.__version__)
print("NumPy:", np.__version__)
print("PyProj:", pyproj.__version__)
print("Shapely:", shapely.__version__)
print("Pillow:", Image.__version__)
print("Environment OK!")