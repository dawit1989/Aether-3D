#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_analysis.py
================
Unit tests for the 3DANTS analysis sub-package.

These tests verify the reusable analysis utilities extracted from the
3DANTS network-with-traffic example: CDF helpers, interference detection,
traffic-model factories, visibility computations, plotting, and the
component registry.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO)

import importlib
_analysis = importlib.import_module("3DANTS.analysis")


class TestEmpiricalCDF(unittest.TestCase):
    def test_sorted_data_and_yvals(self):
        data = [3, 1, 2]
        sorted_data, yvals = _analysis.empirical_cdf(data)
        np.testing.assert_array_equal(sorted_data, [1, 2, 3])
        np.testing.assert_allclose(yvals, [0, 0.5, 1.0])

    def test_single_sample(self):
        sorted_data, yvals = _analysis.empirical_cdf([42])
        self.assertEqual(len(sorted_data), 1)
        self.assertEqual(len(yvals), 1)

    def test_empty(self):
        sorted_data, yvals = _analysis.empirical_cdf([])
        self.assertEqual(len(sorted_data), 0)
        self.assertEqual(len(yvals), 0)

    def test_plot_cdf_returns_true(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = _analysis.plot_cdf(ax, [1, 2, 3, 4, 5], label="test", color="blue")
        self.assertTrue(result)
        plt.close(fig)

    def test_plot_cdf_empty_returns_false(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = _analysis.plot_cdf(ax, [], label="test", color="blue")
        self.assertFalse(result)
        plt.close(fig)


class TestInterference(unittest.TestCase):
    def test_detect_interference(self):
        vals = [-122.086, -110.0, -122.086]
        result = _analysis.detect_interference(vals)
        np.testing.assert_array_equal(result, [False, True, False])

    def test_noise_floor_value(self):
        self.assertEqual(_analysis.NOISE_FLOOR, -122.086)

    def test_classify_interference(self):
        df = pd.DataFrame({
            "HAPS_rx": [-122.086, -110.0],
            "BaseStation1_rx": [-122.086, -120.0],
            "BaseStation2_rx": [-122.086, -122.086],
            "BaseStation3_rx": [-122.086, -122.086],
        })
        result = _analysis.classify_interference(df)
        self.assertIn("HAPS_active", result.columns)
        self.assertIn("BS1_active", result.columns)
        self.assertIn("BS2_active", result.columns)
        self.assertIn("BS3_active", result.columns)
        self.assertIn("Scenario", result.columns)
        self.assertEqual(result.iloc[0]["Scenario"], "No Interference")
        self.assertEqual(result.iloc[1]["Scenario"], "Two sources: HAPS+BS1")

    def test_classify_does_not_mutate_input(self):
        df = pd.DataFrame({
            "HAPS_rx": [-110.0],
            "BaseStation1_rx": [-122.086],
            "BaseStation2_rx": [-122.086],
            "BaseStation3_rx": [-122.086],
        })
        cols_before = list(df.columns)
        _analysis.classify_interference(df)
        self.assertEqual(list(df.columns), cols_before)


class TestTrafficModels(unittest.TestCase):
    def test_cbr(self):
        model = _analysis.cbr(packet_size=1000, packet_rate=10)
        model.generate_packets(10)
        packets = model.get_packets_at_time(0, time_window=1.0)
        self.assertIsInstance(packets, list)

    def test_poisson(self):
        model = _analysis.poisson(avg_packet_rate=10)
        model.generate_packets(10)
        packets = model.get_packets_at_time(0, time_window=1.0)
        self.assertIsInstance(packets, list)

    def test_bursty(self):
        model = _analysis.bursty()
        model.generate_packets(10)
        packets = model.get_packets_at_time(0, time_window=1.0)
        self.assertIsInstance(packets, list)

    def test_build_traffic_models_keys(self):
        models = _analysis.build_traffic_models(100, 5, haps_rate=10, bs_rates=(10, 8, 5))
        self.assertIn("HAPS", models)
        self.assertIn("BS1", models)
        self.assertIn("BS2", models)
        self.assertIn("BS3", models)
        sat_keys = [k for k in models if k.startswith("Sat ")]
        self.assertEqual(len(sat_keys), 5)


class TestComponentRegistry(unittest.TestCase):
    def test_register_and_get(self):
        reg = _analysis.ComponentRegistry()
        reg.register("cbr", _analysis.cbr)
        self.assertEqual(reg.get("cbr"), _analysis.cbr)
        self.assertIn("cbr", reg)
        self.assertIn("cbr", reg.names())

    def test_register_empty_name_raises(self):
        reg = _analysis.ComponentRegistry()
        with self.assertRaises(ValueError):
            reg.register("", _analysis.cbr)

    def test_register_non_callable_raises(self):
        reg = _analysis.ComponentRegistry()
        with self.assertRaises(TypeError):
            reg.register("test", 42)

    def test_get_missing_raises(self):
        reg = _analysis.ComponentRegistry()
        with self.assertRaises(KeyError):
            reg.get("nonexistent")

    def test_chained_registration(self):
        reg = _analysis.ComponentRegistry()
        reg.register("cbr", _analysis.cbr).register("poisson", _analysis.poisson)
        self.assertEqual(len(reg.names()), 2)


class TestVisibility(unittest.TestCase):
    def test_compute_simultaneous_visibility(self):
        df = pd.DataFrame({
            "Satellite": ["Sat 1", "Sat 2"],
            "Rise": [datetime(2022, 9, 22, 0, 0, 0), datetime(2022, 9, 22, 0, 5, 0)],
            "Set": [datetime(2022, 9, 22, 0, 10, 0), datetime(2022, 9, 22, 0, 15, 0)],
        })
        result = _analysis.compute_simultaneous_visibility(
            df, datetime(2022, 9, 22, 0, 0, 0), datetime(2022, 9, 22, 0, 20, 0)
        )
        self.assertIn("group", result.columns)
        self.assertIn("duration_min", result.columns)
        self.assertGreater(len(result), 0)

    def test_visibility_summary(self):
        df = pd.DataFrame({
            "Satellite": ["Sat 1", "Sat 2"],
            "Rise": [pd.Timestamp("2022-09-22 00:00:00"), pd.Timestamp("2022-09-22 00:05:00")],
            "Set": [pd.Timestamp("2022-09-22 00:30:00"), pd.Timestamp("2022-09-22 01:00:00")],
            "Visibility": [pd.Timedelta(minutes=30), pd.Timedelta(minutes=55)],
        })
        result = _analysis.visibility_summary(df)
        self.assertIn("Satellite", result.columns)
        self.assertIn("Visibility", result.columns)
        self.assertEqual(len(result), 2)


class TestPlotting(unittest.TestCase):
    def test_plot_visibility_bars(self):
        summary = pd.DataFrame({
            "Satellite": ["Sat 1", "Sat 2"],
            "Visibility": [30.0, 55.0],
        })
        ax = _analysis.plot_visibility_bars(summary)
        self.assertIsNotNone(ax)

    def test_plot_network_geometry(self):
        cell_vertices = np.array([[0, 1, 2], [0, 1, 2]])
        bs_positions = [np.array([0.5, 0.5]), np.array([1.5, 1.5])]
        haps_pos = np.array([[0.3, 0.3]])
        ax = _analysis.plot_network_geometry(
            cell_vertices, np.array([0, 0]), np.array([0.5, 0.5]),
            bs_positions, haps_pos
        )
        self.assertIsNotNone(ax)

    def test_plot_interference_cdf(self):
        df = pd.DataFrame({
            "HAPS_rx": [-110, -115, -120],
            "BaseStation1_rx": [-120, -118, -115],
            "BaseStation2_rx": [-122, -122, -122],
            "BaseStation3_rx": [-122, -122, -122],
        })
        ax = _analysis.plot_interference_cdf(df)
        self.assertIsNotNone(ax)


if __name__ == "__main__":
    unittest.main()
