# Compatibility shim - re-exports from modularized package.
import os as _os, sys as _sys, importlib as _il
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
if _pkg_root not in _sys.path:
    _sys.path.insert(0, _pkg_root)
_m = _il.import_module('3DANTS.position_and_mobility.ppp_scenario')
truncated_cone_volume = _m.truncated_cone_volume
HAPS_circular_trajectory = _m.HAPS_circular_trajectory
is_inside_half_spheroid = _m.is_inside_half_spheroid
is_inside_cylinder = _m.is_inside_cylinder
create_cylinder = _m.create_cylinder
__all__ = ['truncated_cone_volume', 'HAPS_circular_trajectory', 'is_inside_half_spheroid', 'is_inside_cylinder', 'create_cylinder']
