import os as _os

N_BUNCHES = 2760
REVOLUTION_FREQUENCY = 11246
RATE_NORM_FACTOR = N_BUNCHES * REVOLUTION_FREQUENCY / 1000  # in kHz

# Directory holding the parquet caches (cache/<version>/...). Override with the
# environment variable MENU_TOOLS_CACHE, e.g. to write into a different area
# than the one the repo's `cache` symlink points to.
CACHE_DIR = _os.environ.get("MENU_TOOLS_CACHE", "cache")
# Decimals the P2GT emulator menus keep of each scaling parameter
P2GT_DECIMALS = 2
