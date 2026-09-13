#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_czml_writer.py
===================
Unit tests for the CZML writer that converts orchestrator simulation
results into Cesium Markup Language files.

The writer is framework-agnostic (duck-types SimulationResults),
so we construct lightweight mock results with SimpleNamespace and
pandas DataFrames — no skyfield/sgp4 needed.
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Import CZMLWriter directly from the module file to avoid triggering
# analysis/__init__.py which imports heavy subpackages.
# ---------------------------------------------------------------------------
_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

_spec = importlib.util.spec_from_file_location(
    "czml_writer",
    os.path.join(_REPO, "3DANTS", "analysis", "czml_writer.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CZMLWriter = _mod.CZMLWriter


# ---------------------------------------------------------------------------
# Mock data helpers
# ---------------------------------------------------------------------------

def make_mock_config():
    """Minimal config with the fields the CZML writer reads."""
    return SimpleNamespace(
        gs_lat=53.110987,
        gs_lon=8.851239,
        r_E=6371e3,          # meters
        cell_radius_km=25.0,
    )


def make_mock_results():
    """Create mock SimulationResults with two satellites and three steps."""
    cfg = make_mock_config()

    t0 = datetime(2022, 9, 22, 0, 0, 0)
    t1 = datetime(2022, 9, 22, 0, 0, 1)
    t2 = datetime(2022, 9, 22, 0, 0, 2)

    sat_position = pd.DataFrame([
        {"Satellite ID": 1, "Time": t0,
         "Sat Position (km)": np.array([7000.0, 0.0, 0.0])},
        {"Satellite ID": 1, "Time": t1,
         "Sat Position (km)": np.array([6900.0, 1000.0, 0.0])},
        {"Satellite ID": 1, "Time": t2,
         "Sat Position (km)": np.array([6800.0, 2000.0, 0.0])},
        {"Satellite ID": 2, "Time": t0,
         "Sat Position (km)": np.array([0.0, 7000.0, 0.0])},
        {"Satellite ID": 2, "Time": t1,
         "Sat Position (km)": np.array([0.0, 6900.0, 1000.0])},
        {"Satellite ID": 2, "Time": t2,
         "Sat Position (km)": np.array([0.0, 6800.0, 2000.0])},
    ])

    p_rx = pd.DataFrame([
        {"Satellite ID": 1, "Time": t0, "P_rx_at_User (dBW)": -80.0,
         "SNR (dB)": 5.0, "Distance (km)": 1000.0},
        {"Satellite ID": 1, "Time": t1, "P_rx_at_User (dBW)": -85.0,
         "SNR (dB)": 0.0, "Distance (km)": 1100.0},
        {"Satellite ID": 1, "Time": t2, "P_rx_at_User (dBW)": -90.0,
         "SNR (dB)": -5.0, "Distance (km)": 1200.0},
        {"Satellite ID": 2, "Time": t0, "P_rx_at_User (dBW)": -70.0,
         "SNR (dB)": 15.0, "Distance (km)": 800.0},
        {"Satellite ID": 2, "Time": t1, "P_rx_at_User (dBW)": -75.0,
         "SNR (dB)": 10.0, "Distance (km)": 900.0},
        {"Satellite ID": 2, "Time": t2, "P_rx_at_User (dBW)": -80.0,
         "SNR (dB)": 5.0, "Distance (km)": 1000.0},
    ])

    sat_orbital = pd.DataFrame([
        {"Satellite ID": 1, "Time": t0,
         "Theta_el_sat_see_vsat": 45.0, "Theta_az_sat_see_vsat": 90.0,
         "theta_el_vsat_see_sat": 30.0, "theta_az_vsat_see_sat": 60.0},
        {"Satellite ID": 1, "Time": t1,
         "Theta_el_sat_see_vsat": 50.0, "Theta_az_sat_see_vsat": 95.0,
         "theta_el_vsat_see_sat": 35.0, "theta_az_vsat_see_sat": 65.0},
        {"Satellite ID": 1, "Time": t2,
         "Theta_el_sat_see_vsat": 55.0, "Theta_az_sat_see_vsat": 100.0,
         "theta_el_vsat_see_sat": 40.0, "theta_az_vsat_see_sat": 70.0},
        {"Satellite ID": 2, "Time": t0,
         "Theta_el_sat_see_vsat": 40.0, "Theta_az_sat_see_vsat": 80.0,
         "theta_el_vsat_see_sat": 25.0, "theta_az_vsat_see_sat": 55.0},
        {"Satellite ID": 2, "Time": t1,
         "Theta_el_sat_see_vsat": 45.0, "Theta_az_sat_see_vsat": 85.0,
         "theta_el_vsat_see_sat": 30.0, "theta_az_vsat_see_sat": 60.0},
        {"Satellite ID": 2, "Time": t2,
         "Theta_el_sat_see_vsat": 50.0, "Theta_az_sat_see_vsat": 90.0,
         "theta_el_vsat_see_sat": 35.0, "theta_az_vsat_see_sat": 65.0},
    ])

    interference = pd.DataFrame([
        {"Satellite ID": 1, "Time": t0, "SINR (dB)": 4.0},
        {"Satellite ID": 1, "Time": t1, "SINR (dB)": -1.0},
        {"Satellite ID": 1, "Time": t2, "SINR (dB)": -6.0},
        {"Satellite ID": 2, "Time": t0, "SINR (dB)": 14.0},
        {"Satellite ID": 2, "Time": t1, "SINR (dB)": 9.0},
        {"Satellite ID": 2, "Time": t2, "SINR (dB)": 4.0},
    ])

    return SimpleNamespace(
        sat_position=sat_position,
        sat_orbital_params=sat_orbital,
        satellite_channel_time_series=pd.DataFrame(),
        p_rx=p_rx,
        interference=interference,
        visibility=pd.DataFrame(),
        config=cfg,
    )


def _find_entity(entities, entity_id):
    """Return the entity dict with the given id, or None."""
    for e in entities:
        if e.get("id") == entity_id:
            return e
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCZMLWriterBasic(unittest.TestCase):

    def setUp(self):
        self.writer = CZMLWriter(make_mock_results())
        self.entities = json.loads(self.writer.to_czml())

    def test_valid_czml_json(self):
        """Output must be a parseable JSON array."""
        data = json.loads(self.writer.to_czml())
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_document_entity(self):
        """The first entity must be the CZML document with id/version/epoch."""
        doc = self.entities[0]
        self.assertEqual(doc["id"], "document")
        self.assertIn("version", doc)
        self.assertIn("epoch", doc)
        self.assertEqual(doc["epoch"], "2022-09-22T00:00:00Z")

    def test_ground_station_entity(self):
        """Ground station must have a fixed cartesian ECEF position."""
        gs = _find_entity(self.entities, "ground_station")
        self.assertIsNotNone(gs)
        self.assertIn("point", gs)
        self.assertIn("position", gs)
        pos = gs["position"]["cartesian"]
        self.assertEqual(len(pos), 3)
        # Northern hemisphere → z > 0
        self.assertGreater(pos[2], 0)

    def test_satellite_path_entity(self):
        """Each satellite must have a time-dynamic position with cartesian4."""
        sat = _find_entity(self.entities, "sat_1")
        self.assertIsNotNone(sat)
        pos = sat["position"]
        self.assertIn("epoch", pos)
        self.assertIn("cartesian4", pos)
        # 3 positions × (x, y, z, time) = 12 values
        self.assertEqual(len(pos["cartesian4"]), 12)

    def test_coverage_polygon_entity(self):
        """Coverage polygon must have cartographicDegrees with circle vertices."""
        cov = _find_entity(self.entities, "coverage_sat_1")
        self.assertIsNotNone(cov)
        poly = cov["polygon"]
        self.assertIn("positions", poly)
        cd = poly["positions"]["cartographicDegrees"]
        # 3 time steps × (1 time + 16 vertices × 3 coords) = 3 × 49 = 147
        self.assertEqual(len(cd), 3 * (1 + 16 * 3))

    def test_entity_count(self):
        """Expect: document + GS + 2 sats + 2 coverage = 6 entities."""
        self.assertEqual(len(self.entities), 6)


class TestCZMLWriterProperties(unittest.TestCase):

    def setUp(self):
        self.writer = CZMLWriter(make_mock_results())
        self.entities = json.loads(self.writer.to_czml())

    def test_entity_properties(self):
        """Satellite entity must carry mean PRx, SNR, SINR, and orbital angles."""
        sat = _find_entity(self.entities, "sat_1")
        props = sat["properties"]
        self.assertIn("meanPRx", props)
        self.assertIn("meanSNR", props)
        self.assertIn("meanSINR", props)
        self.assertIn("mean_Theta_el_sat_see_vsat", props)

    def test_prx_color_coding(self):
        """Satellites with different mean P_Rx must have different path colours."""
        sat1 = _find_entity(self.entities, "sat_1")
        sat2 = _find_entity(self.entities, "sat_2")
        color1 = sat1["path"]["material"]["solidColor"]["color"]["rgba"]
        color2 = sat2["path"]["material"]["solidColor"]["color"]["rgba"]
        self.assertNotEqual(color1, color2)

    def test_sat2_prx_value(self):
        """Satellite 2 mean P_Rx should be -75 dBW."""
        sat = _find_entity(self.entities, "sat_2")
        self.assertAlmostEqual(sat["properties"]["meanPRx"]["number"], -75.0,
                               places=2)


class TestCZMLWriterEdgeCases(unittest.TestCase):

    def test_empty_results(self):
        """Results = None should still produce a valid (minimal) CZML doc."""
        writer = CZMLWriter(None)
        data = json.loads(writer.to_czml())
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "document")

    def test_write_to_file(self):
        """write() should create a file that round-trips as valid JSON."""
        writer = CZMLWriter(make_mock_results())
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.czml")
            returned_path = writer.write(path)
            self.assertEqual(returned_path, path)
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)


class TestCZMLWriterHelpers(unittest.TestCase):

    def test_pwr_to_rgba_returns_4_ints(self):
        """_pwr_to_rgba must return a 4-element RGBA list."""
        rgba = _mod._pwr_to_rgba(-80.0)
        self.assertEqual(len(rgba), 4)
        for v in rgba:
            self.assertIsInstance(v, int)

    def test_pwr_to_rgba_range(self):
        """Extreme P_Rx values should map to valid RGBA."""
        low = _mod._pwr_to_rgba(-120.0)
        high = _mod._pwr_to_rgba(-60.0)
        self.assertEqual(len(low), 4)
        self.assertEqual(len(high), 4)

    def test_sub_satellite_latlon_equator(self):
        """Position on the equator at lon=0 should give lat=0, lon=0."""
        lat, lon = _mod._sub_satellite_latlon(7000e3, 0, 0)
        self.assertAlmostEqual(lat, 0.0, places=4)
        self.assertAlmostEqual(lon, 0.0, places=4)

    def test_sub_satellite_latlon_90east(self):
        """Position at lon=90°E should give lon=90."""
        lat, lon = _mod._sub_satellite_latlon(0, 7000e3, 0)
        self.assertAlmostEqual(lat, 0.0, places=4)
        self.assertAlmostEqual(lon, 90.0, places=4)

    def test_coverage_circle_vertex_count(self):
        """Coverage circle with n=16 must produce 48 values (16 × 3)."""
        circle = _mod._coverage_circle(0.0, 0.0, 25.0, 16)
        self.assertEqual(len(circle), 48)

    def test_ecef_km_to_m(self):
        """Positions must be scaled by 1000."""
        pos_m = _mod._ecef_km_to_m([1.0, 2.0, 3.0])
        np.testing.assert_array_equal(pos_m, [1000.0, 2000.0, 3000.0])


if __name__ == "__main__":
    unittest.main()
