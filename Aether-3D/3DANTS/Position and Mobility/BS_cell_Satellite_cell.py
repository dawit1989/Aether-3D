# Compatibility shim - re-exports from modularized package.
import os as _os, sys as _sys, importlib as _il
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
if _pkg_root not in _sys.path:
    _sys.path.insert(0, _pkg_root)
_m = _il.import_module('3DANTS.position_and_mobility.satellite_cell_geom')
hexagon_vertices = _m.hexagon_vertices
compute_new_hexagon_center = _m.compute_new_hexagon_center
vertices_sorting = _m.vertices_sorting
sort_vertices_counterclockwise = _m.sort_vertices_counterclockwise
north_edge = _m.north_edge
plot_hexagon = _m.plot_hexagon
calculate_midpoint = _m.calculate_midpoint
overlapping_rhombus = _m.overlapping_rhombus
plot_two_hexagons = _m.plot_two_hexagons
highlight_rhombus = _m.highlight_rhombus
__all__ = ['hexagon_vertices', 'compute_new_hexagon_center', 'vertices_sorting', 'sort_vertices_counterclockwise', 'north_edge', 'plot_hexagon', 'calculate_midpoint', 'overlapping_rhombus', 'plot_two_hexagons', 'highlight_rhombus']
