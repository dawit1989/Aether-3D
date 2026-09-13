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
GEOLayer = _sim.GEOLayer
AirObjectsLayer = _sim.AirObjectsLayer
FrequencySelectiveLayer = _sim.FrequencySelectiveLayer
PPPInterferenceLayer = _sim.PPPInterferenceLayer
GaussianFieldLayer = _sim.GaussianFieldLayer
AtmosphericLossLayer = _sim.AtmosphericLossLayer
SatelliteCellGeomLayer = _sim.SatelliteCellGeomLayer
NTNFadingLayer = _sim.NTNFadingLayer
ConstellationLayer = _sim.ConstellationLayer
SphereUtilLayer = _sim.SphereUtilLayer
BaseFadingLayer = _sim.BaseFadingLayer


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



class TestNewConfigFields(unittest.TestCase):
    def test_cell_radius_km_default(self):
        cfg = SimulationConfig()
        self.assertEqual(cfg.cell_radius_km, 25.0)

    def test_geo_config_defaults(self):
        cfg = SimulationConfig()
        self.assertFalse(cfg.geo_enabled)
        self.assertEqual(cfg.geo_inclination, 0)
        self.assertEqual(cfg.geo_count, 3)

    def test_air_config_defaults(self):
        cfg = SimulationConfig()
        self.assertEqual(cfg.air_environment, "Suburban")
        self.assertEqual(cfg.air_altitude, 10.0)

    def test_fs_config_defaults(self):
        cfg = SimulationConfig()
        self.assertEqual(cfg.fs_num_subcarriers, 64)
        self.assertEqual(cfg.fs_delay_spread, 1e-6)
        self.assertEqual(cfg.fs_num_taps, 8)

    def test_ppp_config_defaults(self):
        cfg = SimulationConfig()
        self.assertEqual(cfg.ppp_lambda, 10)
        self.assertEqual(cfg.ppp_radius, 10.0)

    def test_gf_config_defaults(self):
        cfg = SimulationConfig()
        self.assertEqual(cfg.gf_variance, 8.0)
        self.assertEqual(cfg.gf_len_scale, 0.01)

    def test_atmospheric_config_defaults(self):
        cfg = SimulationConfig()
        self.assertFalse(cfg.detailed_atmospheric_loss)


class TestNewLayersRegistration(unittest.TestCase):
    def test_new_layers_registered(self):
        sim = NetworkSimulation()
        names = sim.registry.names()
        for name in ["geo", "air_objects", "freq_selective", "ppp",
                     "gaussian_field", "atmospheric_loss",
                     "satellite_cell_geom", "ntn_fading",
                     "constellation", "sphere_util", "base_fading"]:
            self.assertIn(name, names, f"{name} not registered")

    def test_layer_names(self):
        self.assertEqual(GEOLayer.name, "geo")
        self.assertEqual(AirObjectsLayer.name, "air_objects")
        self.assertEqual(FrequencySelectiveLayer.name, "freq_selective")
        self.assertEqual(PPPInterferenceLayer.name, "ppp")
        self.assertEqual(GaussianFieldLayer.name, "gaussian_field")
        self.assertEqual(AtmosphericLossLayer.name, "atmospheric_loss")
        self.assertEqual(SatelliteCellGeomLayer.name, "satellite_cell_geom")
        self.assertEqual(NTNFadingLayer.name, "ntn_fading")
        self.assertEqual(ConstellationLayer.name, "constellation")
        self.assertEqual(SphereUtilLayer.name, "sphere_util")
        self.assertEqual(BaseFadingLayer.name, "base_fading")


class TestNewFluentMethods(unittest.TestCase):
    def test_with_geo(self):
        sim = NetworkSimulation()
        sim.with_geo(count=5, inclination=70)
        self.assertTrue(sim.cfg.geo_enabled)
        self.assertEqual(sim.cfg.geo_count, 5)
        self.assertEqual(sim.cfg.geo_inclination, 70)
        self.assertIn("geo", sim.registry.names())
        self.assertEqual(len(sim.layers), 8)

    def test_with_air_objects(self):
        sim = NetworkSimulation()
        sim.with_air_objects(environment="Urban")
        self.assertEqual(sim.cfg.air_environment, "Urban")
        self.assertIn("air_objects", sim.registry.names())
        self.assertEqual(len(sim.layers), 8)

    def test_with_freq_selective(self):
        sim = NetworkSimulation()
        sim.with_freq_selective(num_subcarriers=128, delay_spread=2e-6, num_taps=16)
        self.assertEqual(sim.cfg.fs_num_subcarriers, 128)
        self.assertEqual(sim.cfg.fs_delay_spread, 2e-6)
        self.assertEqual(sim.cfg.fs_num_taps, 16)
        self.assertIn("freq_selective", sim.registry.names())

    def test_with_ppp(self):
        sim = NetworkSimulation()
        sim.with_ppp(lam=20, radius=15.0)
        self.assertEqual(sim.cfg.ppp_lambda, 20)
        self.assertEqual(sim.cfg.ppp_radius, 15.0)
        self.assertIn("ppp", sim.registry.names())

    def test_with_gaussian_field(self):
        sim = NetworkSimulation()
        sim.with_gaussian_field(variance=10.0, len_scale=0.02)
        self.assertEqual(sim.cfg.gf_variance, 10.0)
        self.assertEqual(sim.cfg.gf_len_scale, 0.02)
        self.assertIn("gaussian_field", sim.registry.names())

    def test_with_atmospheric_loss(self):
        sim = NetworkSimulation()
        sim.with_atmospheric_loss(detailed=True)
        self.assertTrue(sim.cfg.detailed_atmospheric_loss)
        self.assertIn("atmospheric_loss", sim.registry.names())

    def test_with_satellite_cell_geom(self):
        sim = NetworkSimulation()
        sim.with_satellite_cell_geom(radius_km=50.0)
        self.assertEqual(sim.cfg.cell_radius_km, 50.0)
        self.assertIn("satellite_cell_geom", sim.registry.names())

    def test_with_ntn_fading(self):
        sim = NetworkSimulation()
        sim.with_ntn_fading()
        self.assertIn("ntn_fading", sim.registry.names())
        self.assertEqual(len(sim.layers), 8)

    def test_fluent_returns_self_for_new_methods(self):
        sim = NetworkSimulation()
        for result in [
            sim.with_geo(),
            sim.with_atmospheric_loss(),
            sim.with_satellite_cell_geom(),
            sim.with_constellation_layer(),
            sim.with_sphere_util(),
            sim.with_base_fading(),
        ]:
            self.assertIs(result, sim)

    def test_with_constellation_layer(self):
        sim = NetworkSimulation()
        sim.with_constellation_layer()
        self.assertIn("constellation", sim.registry.names())
        self.assertEqual(len(sim.layers), 8)

    def test_with_sphere_util(self):
        sim = NetworkSimulation()
        sim.with_sphere_util()
        self.assertIn("sphere_util", sim.registry.names())

    def test_with_base_fading(self):
        sim = NetworkSimulation()
        sim.with_base_fading()
        self.assertIn("base_fading", sim.registry.names())


class TestLayerHooks(unittest.TestCase):
    def test_new_layers_are_simlayer_subclasses(self):
        for cls in [GEOLayer, AirObjectsLayer, FrequencySelectiveLayer,
                    PPPInterferenceLayer, GaussianFieldLayer,
                    AtmosphericLossLayer, SatelliteCellGeomLayer, NTNFadingLayer,
                    ConstellationLayer, SphereUtilLayer, BaseFadingLayer]:
            self.assertTrue(issubclass(cls, SimLayer))

    def test_new_layer_configure_sets_sim(self):
        for layer_cls in [AtmosphericLossLayer, SatelliteCellGeomLayer,
                          NTNFadingLayer, PPPInterferenceLayer,
                          ConstellationLayer, SphereUtilLayer, BaseFadingLayer]:
            layer = layer_cls()
            sim = NetworkSimulation()
            layer.configure(sim)
            self.assertIs(layer.sim, sim)


if __name__ == "__main__":
    unittest.main()
