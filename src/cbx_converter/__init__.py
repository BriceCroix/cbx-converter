import importlib.metadata

try:
    __version__ = importlib.metadata.version("cbx-converter")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for an uninstalled source tree
