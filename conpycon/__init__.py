"""
File:
    conpycon/__init__.py

Brief:
    ConPyCon - A Configurable Python Console.
"""

import pkgutil
import sys

__all__ = [
    '__version__',
]

# ConPyCon versions.
__version__ = (pkgutil.get_data(__package__, "VERSION") or b"").decode('ascii').strip()
version_info = tuple(int(v) if v.isdigit() else v for v in __version__.split("."))

# Check minimum required python version.
if sys.version_info < (3, 7):
    print(f"ConPyCon {__version__} requires Python 3.7+")
    sys.exit(1)

del pkgutil
del sys
