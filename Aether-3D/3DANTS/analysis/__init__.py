"""3DANTS analysis sub-package.

Reusable, framework-independent analysis utilities extracted from the
3DANTS network-with-traffic example:

- visibility overlap and per-satellite visibility summaries
- interference detection and scenario classification
- SINR computation and summary statistics
- throughput and spectral-efficiency helpers
- coverage-probability helpers
- empirical CDF computation and plotting
- traffic-model construction helpers
- reusable matplotlib plotting helpers
- a lightweight component registry

The orchestrator (``examples/3D_network_with_traffic``) imports these instead
of embedding the logic inline.
"""
from .visibility import compute_simultaneous_visibility, visibility_summary
from .interference import detect_interference, classify_interference, NOISE_FLOOR
from .sinr import compute_sinr, sinr_summary, outage_probability
from .throughput import spectral_efficiency, mean_throughput, throughput_cdf
from .coverage import coverage_probability, coverage_vs_elevation
from .cdf import empirical_cdf, plot_cdf
from .traffic import cbr, poisson, bursty, build_traffic_models
from .plotting import plot_visibility_bars, plot_network_geometry, plot_interference_cdf
from ._registry import ComponentRegistry
from .czml_writer import CZMLWriter

__all__ = [
    "compute_simultaneous_visibility",
    "visibility_summary",
    "detect_interference",
    "classify_interference",
    "NOISE_FLOOR",
    "compute_sinr",
    "sinr_summary",
    "outage_probability",
    "spectral_efficiency",
    "mean_throughput",
    "throughput_cdf",
    "coverage_probability",
    "coverage_vs_elevation",
    "empirical_cdf",
    "plot_cdf",
    "cbr",
    "poisson",
    "bursty",
    "build_traffic_models",
    "plot_visibility_bars",
    "plot_network_geometry",
    "plot_interference_cdf",
    "ComponentRegistry",
    "CZMLWriter",
]
