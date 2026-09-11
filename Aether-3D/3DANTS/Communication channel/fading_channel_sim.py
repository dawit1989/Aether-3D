# Compatibility shim - re-exports from modularized package.
import os as _os, sys as _sys, importlib as _il
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
if _pkg_root not in _sys.path:
    _sys.path.insert(0, _pkg_root)
_m = _il.import_module('3DANTS.communication_channel.fading_channel_sim')
FadingSimulation = _m.FadingSimulation
__all__ = ['FadingSimulation']
