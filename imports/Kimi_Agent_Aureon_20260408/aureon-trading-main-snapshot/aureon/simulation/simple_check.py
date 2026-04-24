
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
print(f"Python: {sys.executable}")
try:
    import numpy
    print(f"Numpy: {numpy.__version__}")
except ImportError as e:
    print(f"Numpy Import Failed: {e}")
