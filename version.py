"""
Aureon Trading System Version
"""

__version__ = "0.9.0-beta"
__codename__ = "Four Battlefronts"
__release_date__ = "2025-12-29"

VERSION_INFO = {
    "version": __version__,
    "codename": __codename__,
    "release_date": __release_date__,
    "status": "beta",
    "exchanges": ["binance", "kraken", "capital", "alpaca"],
}

def get_version():
    """Return the current version string."""
    return __version__

def get_version_info():
    """Return full version information."""
    return VERSION_INFO

if __name__ == "__main__":
    print(f"Aureon Trading System v{__version__}")
    print(f"Codename: {__codename__}")
    print(f"Released: {__release_date__}")
