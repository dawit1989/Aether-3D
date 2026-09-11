#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_simulation.py
==================
Integration tests for the layer-based orchestrator
(``examples/3D_network_with_traffic.py``).

Heavy optional imports (skyfield, sgp4, sympy, progress) are mocked so the
layer structure, fluent API, and ComponentRegistry can be tested without a
full orbital-propagation environment.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Silence heavy optional imports that are not needed for these tests
# ---------------------------------------------------------------------------
for _mod in ['skyfield', 'skyfield.api', 'sgp4', 'sgp4.api',
             'sympy', 'progress', 'progress.bar']:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, _REPO)
sys.path.insert(0, os.path.join(_REPO, 'examples'))

import importlib
_sim = importlib.import_module('3D_network_with_traffic')

NetworkSimulation = _sim.NetworkSimulation
SimulationConfig = _sim.SimulationConfig
SimLayer = _sim.SimLayer
UAVLayer = _sim.UAVLayer
ComponentRegistry = _sim.ComponentRegistry


class TestSimulationConfig(unittest.TestCase):
    def test_defaults_match_engine(self):
        cfg = SimulationConfig()
        self.assertEqual(cfg.h_leo, 600e3)
        self.assertEqual(cfg.inclination, 60)
        self.assertEqual(cfg.num_sat, 120)
        self.assertEqual(cfg.num_planes, 10)
        self.assertEqual(cfg.phasing, 1)
        self.assertEqual(cfg.r_E, 6371e3)
        self.assertEqual(cfg.gm, 3.986004418e14)
        self.assertEqual(cfg.h_GEO, 20000e3)
        self.assertEqual(cfg.f, 2.0e9)
        self.assertEqual(cfg.gs_lat, 53.110987)
        self.assertEqual(cfg.gs_lon, 8.851239)
        self.assertEqual(cfg.noise_figure_db, 7.0)
        self.assertEqual(cfg.temperature_k, 25 + 273.15)
        self.assertEqual(cfg.num_base_stations, 3)
        self.assertIsNone(cfg.steps)
        self.assertFalse(cfg.plot)
        self.assertFalse(cfg.verbose)

    def test_uav_defaults(self):
        cfg = SimulationConfig()
        self.assertEqual(cfg.uav_height, 0.1)
        self.assertEqual(cfg.uav_velocity, 18.0)

    def test_dataclass_fields(self):
        cfg = SimulationConfig(h_leo=800e3, num_sat=60)
        self.assertEqual(cfg.h_leo, 800e3)
        self.assertEqual(cfg.num_sat, 60)


class TestNetworkSimulationLayers(unittest.TestCase):
    def test_default_layers(self):
        sim = NetworkSimulation()
        names = [l.name for l in sim.layers]
        self.assertEqual(names, [
            "geometry", "fading", "shadowing", "traffic",
            "haps", "base_station", "interference",
        ])

    def test_layer_count(self):
        sim = NetworkSimulation()
        self.assertEqual(len(sim.layers), 7)

    def test_default_layer_order(self):
        self.assertEqual(NetworkSimulation.DEFAULT_LAYER_ORDER, [
            "geometry", "fading", "shadowing", "traffic",
            "haps", "base_station", "interference",
        ])


class TestComponentRegistry(unittest.TestCase):
    def test_registry_populated(self):
        sim = NetworkSimulation()
        names = sim.registry.names()
        self.assertIn("geometry", names)
        self.assertIn("fading", names)
        self.assertIn("interference", names)

    def test_resolve_layer(self):
        sim = NetworkSimulation()
        layer = sim._resolve_layer("geometry")
        self.assertIsInstance(layer, SimLayer)
        self.assertEqual(layer.name, "geometry")

    def test_add_layer_registers(self):
        sim = NetworkSimulation()
        sim.add_layer(UAVLayer())
        self.assertIn("uav", sim.registry.names())
        self.assertEqual(len(sim.layers), 8)


class TestFluentConfig(unittest.TestCase):
    def test_with_constellation(self):
        sim = NetworkSimulation()
        sim.with_constellation(h_leo=800e3, num_sat=60, num_planes=5, inclination=55)
        self.assertEqual(sim.cfg.h_leo, 800e3)
        self.assertEqual(sim.cfg.num_sat, 60)
        self.assertEqual(sim.cfg.num_planes, 5)
        self.assertEqual(sim.cfg.inclination, 55)

    def test_with_ground_station(self):
        sim = NetworkSimulation()
        sim.with_ground_station(lat=40.0, lon=-100.0)
        self.assertEqual(sim.cfg.gs_lat, 40.0)
        self.assertEqual(sim.cfg.gs_lon, -100.0)

    def test_with_fading(self):
        sim = NetworkSimulation()
        sim.with_fading(mode="scaled", fc=2.6e9)
        self.assertEqual(sim.cfg.fading_mode, "scaled")
        self.assertEqual(sim.cfg.f, 2.6e9)

    def test_with_traffic(self):
        sim = NetworkSimulation()
        sim.with_traffic(num_sat=200, haps_rate=20, bs_rates=[5, 3, 2])
        self.assertEqual(sim.cfg.num_sat, 200)
        self.assertEqual(sim.cfg.haps_rate, 20)
        self.assertEqual(sim.cfg.bs_rates, (5, 3, 2))

    def test_with_haps(self):
        sim = NetworkSimulation()
        sim.with_haps(height=15.0, velocity=30.0)
        self.assertEqual(sim.cfg.haps_height, 15.0)
        self.assertEqual(sim.cfg.haps_velocity, 30.0)

    def test_with_base_stations(self):
        sim = NetworkSimulation()
        sim.with_base_stations(n=5)
        self.assertEqual(sim.cfg.num_base_stations, 5)

    def test_with_uav(self):
        sim = NetworkSimulation()
        sim.with_uav(height=0.5, velocity=20.0)
        self.assertEqual(sim.cfg.uav_height, 0.5)
        self.assertEqual(sim.cfg.uav_velocity, 20.0)

    def test_fluent_returns_self(self):
        sim = NetworkSimulation()
        result = sim.with_constellation(h_leo=800e3)
        self.assertIs(result, sim)
        result = sim.with_uav(height=0.5)
        self.assertIs(result, sim)

    def test_with_registry(self):
        sim = NetworkSimulation()
        reg = ComponentRegistry()
        reg.register("custom", UAVLayer)
        sim.with_registry(reg)
        self.assertIs(sim.registry, reg)
        self.assertIn("custom", sim.registry.names())


class TestSimLayerHooks(unittest.TestCase):
    def test_begin_end_pass_noop_by_default(self):
        class DummyLayer(SimLayer):
            name = "dummy"
        layer = DummyLayer()
        layer.begin_pass(None)
        layer.end_pass(None)

    def test_configure_template_method(self):
        class DummyLayer(SimLayer):
            name = "dummy"
            configured = False
            pass_count = 0

            def _configure(self, sim):
                self.configured = True

            def _configure_pass(self, sim):
                self.pass_count += 1
        layer = DummyLayer()
        sim = NetworkSimulation()
        layer.configure(sim)
        self.assertTrue(layer.configured)
        self.assertEqual(layer.pass_count, 1)
        layer.configure(sim)
        self.assertEqual(layer.pass_count, 2)


if __name__ == "__main__":
    unittest.main()
