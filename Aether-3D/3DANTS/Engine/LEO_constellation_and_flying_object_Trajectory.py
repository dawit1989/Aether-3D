# Compatibility shim - runs the modularized script as __main__.
import os as _os, sys as _sys, runpy as _runpy
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
if _pkg_root not in _sys.path:
    _sys.path.insert(0, _pkg_root)
if __name__ == '__main__':
    _runpy.run_module('3DANTS.Engine.simulation', run_name='__main__')
