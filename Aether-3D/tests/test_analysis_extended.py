#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_analysis_extended.py
========================
Unit tests for the Phase 2 analysis sub-package additions:
SINR computation, throughput/spectral-efficiency, and coverage.
"""

import unittest

import numpy as np
import pandas as pd

import sys
import os

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO)

import importlib
_analysis = importlib.import_module("3DANTS.analysis")


class TestComputeSINR(unittest.TestCase):
    def test_linear_sinr(self):
        # p_rx = 0 dB, noise = 0 dB, interference = -1000 dB -> SINR ~ 1.0
        result = _analysis.compute_sinr([0], [0], -1000)
        np.testing.assert_allclose(result, [1.0])

    def test_with_interference(self):
        # p_rx = 10 dB, noise = 0 dB, interference = 0 dB -> 10/(1+1) = 5
        result = _analysis.compute_sinr([10], [0], [0])
        np.testing.assert_allclose(result, [5.0])

    def test_array_input(self):
        p_rx = [0, 10, 20]
        noise = [0, 0, 0]
        result = _analysis.compute_sinr(p_rx, noise, 0)
        self.assertEqual(len(result), 3)


class TestOutageProbability(unittest.TestCase):
    def test_no_outage(self):
        sinr = [0, 10, 20]
        self.assertEqual(_analysis.outage_probability(sinr, -5.0), 0.0)

    def test_all_outage(self):
        sinr = [-10, -20, -30]
        self.assertEqual(_analysis.outage_probability(sinr, -5.0), 1.0)

    def test_partial_outage(self):
        sinr = [0, -10, 10, -20]
        self.assertEqual(_analysis.outage_probability(sinr, -5.0), 0.5)

    def test_empty(self):
        self.assertEqual(_analysis.outage_probability([], -5.0), 0.0)


class TestSINRSummary(unittest.TestCase):
    def test_summary(self):
        df = pd.DataFrame({"SINR (dB)": [-10, 0, 10, 20, 30]})
        result = _analysis.sinr_summary(df)
        self.assertIn("mean", result)
        self.assertIn("median", result)
        self.assertIn("p05", result)
        self.assertIn("p95", result)
        self.assertIn("outage_prob", result)
        self.assertEqual(result["count"], 5)
        self.assertGreater(result["outage_prob"], 0)  # -10 < -5

    def test_empty_column(self):
        df = pd.DataFrame({"SINR (dB)": []})
        result = _analysis.sinr_summary(df)
        self.assertEqual(result["count"], 0)


class TestSpectralEfficiency(unittest.TestCase):
    def test_known_value(self):
        # SINR = 0 dB -> linear = 1 -> B * log2(2) = B
        se = _analysis.spectral_efficiency([0], 1e6)
        np.testing.assert_allclose(se, [1e6])

    def test_shannon_positive(self):
        se = _analysis.spectral_efficiency([10, 20], 1e6)
        self.assertLess(se[0], se[1])  # higher SINR -> higher SE

    def test_array_output(self):
        se = _analysis.spectral_efficiency([0, 10, 20], 1e6)
        self.assertEqual(len(se), 3)


class TestMeanThroughput(unittest.TestCase):
    def test_mean(self):
        mt = _analysis.mean_throughput([0, 10, 20], 1e6)
        self.assertGreater(mt, 0)

    def test_empty(self):
        self.assertEqual(_analysis.mean_throughput([], 1e6), 0.0)


class TestThroughputCDF(unittest.TestCase):
    def test_cdf_shape(self):
        sorted_data, yvals = _analysis.throughput_cdf([0, 10, 20], 1e6)
        self.assertEqual(len(sorted_data), 3)
        self.assertEqual(len(yvals), 3)
        self.assertAlmostEqual(yvals[0], 0)
        self.assertAlmostEqual(yvals[-1], 1.0)


class TestCoverageProbability(unittest.TestCase):
    def test_all_covered(self):
        sinr = [0, 10, 20]
        self.assertEqual(_analysis.coverage_probability(sinr, -5.0), 1.0)

    def test_none_covered(self):
        sinr = [-10, -20, -30]
        self.assertEqual(_analysis.coverage_probability(sinr, -5.0), 0.0)

    def test_partial(self):
        sinr = [0, -10, 10, -20]
        self.assertEqual(_analysis.coverage_probability(sinr, -5.0), 0.5)

    def test_empty(self):
        self.assertEqual(_analysis.coverage_probability([], -5.0), 0.0)


class TestCoverageVsElevation(unittest.TestCase):
    def test_binned_coverage(self):
        df = pd.DataFrame({
            "Elevation Angle (degree)": [10, 20, 30, 40, 50, 60, 70, 80],
            "SINR (dB)": [10, 15, 20, 25, 30, 35, 40, 45],
        })
        result = _analysis.coverage_vs_elevation(df)
        self.assertIn("elevation_bin", result.columns)
        self.assertIn("coverage_prob", result.columns)
        self.assertIn("count", result.columns)
        self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()
