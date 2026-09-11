#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for the AR(1) large-scale shadow-fading model.

Validates the implementation in:
    3DANTS/communication_channel/shadowing_temporally_correlated_AR.py
against the 3GPP TR 38.811 specification and the mathematical formulation
provided by the user.

Run from repo root:
    pytest tests/test_shadow_fading_ar1.py -v
Or directly:
    python tests/test_shadow_fading_ar1.py
"""

import os
import sys
import math
import unittest

import numpy as np

# ---------------------------------------------------------------------------
# Path setup — the 3DANTS package name starts with a digit, so we add the
# parent directory (the repo root) to sys.path and use importlib.
# ---------------------------------------------------------------------------
_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO)

import importlib
_mod = importlib.import_module(
    "3DANTS.communication_channel.shadowing_temporally_correlated_AR"
)
ShadowingFading = _mod.ShadowingFading


# 3GPP TR 38.811 sigma_SF tables — hard-coded here to serve as a reference
# independent of the implementation under test.
_ELEV_GRID = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0])
_SIGMA_LOS_S  = np.array([1.79, 1.14, 1.14, 0.92, 1.42, 1.56, 0.85, 0.72, 0.72])
_SIGMA_NLOS_S = np.array([8.93, 9.08, 8.78, 10.25, 10.56, 10.74, 10.17, 11.52, 11.52])
_SIGMA_LOS_KA  = np.array([1.9, 1.6, 1.9, 2.3, 2.7, 3.1, 3.0, 3.6, 0.4])
_SIGMA_NLOS_KA = np.array([10.7, 10.0, 11.2, 11.6, 11.8, 10.8, 10.8, 10.8, 10.8])


class TestAR1CorrelationCoefficient(unittest.TestCase):
    """Verify phi = exp(-1 / tau_s) for various tau_s values."""

    def test_phi_formula(self):
        for tau_s in [1, 2, 5, 10, 30, 100]:
            with self.subTest(tau_s=tau_s):
                sf = ShadowingFading(tau=tau_s, N=100)
                expected = math.exp(-1.0 / tau_s)
                self.assertAlmostEqual(sf.phi, expected, places=10)

    def test_phi_zero_tau(self):
        """tau_s = 0 => phi = 0 (no correlation)."""
        sf = ShadowingFading(tau=0, N=100)
        self.assertEqual(sf.phi, 0.0)

    def test_phi_monotonic(self):
        """phi should decrease as tau_s decreases."""
        sf_large = ShadowingFading(tau=100, N=100)
        sf_small = ShadowingFading(tau=1, N=100)
        self.assertGreater(sf_large.phi, sf_small.phi)


class TestSigmaSFLookup(unittest.TestCase):
    """Verify sigma_sf interpolation against reference 3GPP TR 38.811 tables."""

    def _ref_sigma(self, elev, scenario, band):
        el = max(10.0, min(90.0, elev))
        if band == "KaBand":
            tbl = _SIGMA_LOS_KA if scenario == "LOS" else _SIGMA_NLOS_KA
        else:
            tbl = _SIGMA_LOS_S if scenario == "LOS" else _SIGMA_NLOS_S
        return float(np.interp(el, _ELEV_GRID, tbl))

    def test_sband_los_grid_points(self):
        sf = ShadowingFading(tau=10, N=10)
        for el in _ELEV_GRID:
            with self.subTest(el=el):
                got = sf.sigma_sf(el, "LOS", "SBand")
                ref = self._ref_sigma(el, "LOS", "SBand")
                self.assertAlmostEqual(got, ref, places=6)

    def test_sband_nlos_grid_points(self):
        sf = ShadowingFading(tau=10, N=10)
        for el in _ELEV_GRID:
            with self.subTest(el=el):
                got = sf.sigma_sf(el, "NLOS", "SBand")
                ref = self._ref_sigma(el, "NLOS", "SBand")
                self.assertAlmostEqual(got, ref, places=6)

    def test_kaband_los_grid_points(self):
        sf = ShadowingFading(tau=10, N=10)
        for el in _ELEV_GRID:
            with self.subTest(el=el):
                got = sf.sigma_sf(el, "LOS", "KaBand")
                ref = self._ref_sigma(el, "LOS", "KaBand")
                self.assertAlmostEqual(got, ref, places=6)

    def test_kaband_nlos_grid_points(self):
        sf = ShadowingFading(tau=10, N=10)
        for el in _ELEV_GRID:
            with self.subTest(el=el):
                got = sf.sigma_sf(el, "NLOS", "KaBand")
                ref = self._ref_sigma(el, "NLOS", "KaBand")
                self.assertAlmostEqual(got, ref, places=6)

    def test_interpolation_between_grid(self):
        """Linear interpolation should be monotonic between grid points."""
        sf = ShadowingFading(tau=10, N=10)
        val_10 = sf.sigma_sf(10, "LOS", "SBand")
        val_20 = sf.sigma_sf(20, "LOS", "SBand")
        val_15 = sf.sigma_sf(15, "LOS", "SBand")
        self.assertLessEqual(min(val_10, val_20), val_15)
        self.assertGreaterEqual(max(val_10, val_20), val_15)

    def test_elevation_clamping(self):
        """Below 10 deg and above 90 deg should clamp to the table edges."""
        sf = ShadowingFading(tau=10, N=10)
        self.assertAlmostEqual(sf.sigma_sf(5, "LOS", "SBand"), sf.sigma_sf(10, "LOS", "SBand"))
        self.assertAlmostEqual(sf.sigma_sf(100, "LOS", "SBand"), sf.sigma_sf(90, "LOS", "SBand"))


class TestAR1Generator(unittest.TestCase):
    """Validate the AR(1) recursive generator."""

    def test_output_length(self):
        sf = ShadowingFading(tau=10, N=500)
        np.random.seed(42)
        samples = sf.generate_ar1(sigma=1.0)
        self.assertEqual(len(samples), 500)

    def test_zero_mean_finite(self):
        sf = ShadowingFading(tau=10, N=10000)
        np.random.seed(42)
        samples = sf.generate_ar1(sigma=2.0)
        self.assertTrue(np.all(np.isfinite(samples)))
        self.assertAlmostEqual(np.mean(samples), 0.0, delta=0.2)

    def test_marginal_variance(self):
        """The marginal variance should approach sigma^2 for long sequences."""
        sf = ShadowingFading(tau=10, N=50000)
        np.random.seed(42)
        samples = sf.generate_ar1(sigma=3.0)
        empirical_var = np.var(samples)
        self.assertAlmostEqual(empirical_var, 9.0, delta=1.0)

    def test_autocorrelation_lag1(self):
        """Empirical AC(1) should be close to phi = exp(-1/tau_s)."""
        for tau_s in [1, 5, 20]:
            with self.subTest(tau_s=tau_s):
                sf = ShadowingFading(tau=tau_s, N=20000)
                np.random.seed(42)
                samples = sf.generate_ar1(sigma=1.0)
                ac1 = np.corrcoef(samples[:-1], samples[1:])[0, 1]
                expected = math.exp(-1.0 / tau_s)
                self.assertAlmostEqual(ac1, expected, delta=0.03)

    def test_independent_when_phi_zero(self):
        """tau=0 => phi=0 => samples should be uncorrelated."""
        sf = ShadowingFading(tau=0, N=10000)
        np.random.seed(42)
        samples = sf.generate_ar1(sigma=1.0)
        ac1 = np.corrcoef(samples[:-1], samples[1:])[0, 1]
        self.assertAlmostEqual(ac1, 0.0, delta=0.03)

    def test_custom_phi_override(self):
        """generate_ar1 should accept a custom phi."""
        sf = ShadowingFading(tau=10, N=10000)
        np.random.seed(42)
        samples = sf.generate_ar1(sigma=1.0, phi=0.9)
        ac1 = np.corrcoef(samples[:-1], samples[1:])[0, 1]
        self.assertAlmostEqual(ac1, 0.9, delta=0.03)

    def test_custom_n_override(self):
        sf = ShadowingFading(tau=10, N=10000)
        np.random.seed(42)
        samples = sf.generate_ar1(sigma=1.0, n=500)
        self.assertEqual(len(samples), 500)


class TestCovarianceMatrix(unittest.TestCase):
    """Validate the AR(1) covariance matrix R_s."""

    def test_shape_and_diagonal(self):
        sf = ShadowingFading(tau=5, N=10)
        R = sf.covariance_matrix(n=5, phi=0.5, sigma=2.0)
        self.assertEqual(R.shape, (5, 5))
        np.testing.assert_allclose(np.diag(R), 4.0)

    def test_off_diagonal_phi_power(self):
        """[R_s]_{m,n} = phi^|m-n| * sigma^2."""
        sf = ShadowingFading(tau=5, N=10)
        R = sf.covariance_matrix(n=5, phi=0.5, sigma=2.0)
        for i in range(5):
            for j in range(5):
                expected = (0.5 ** abs(i - j)) * 4.0
                self.assertAlmostEqual(R[i, j], expected, places=10)

    def test_symmetric(self):
        sf = ShadowingFading(tau=5, N=10)
        R = sf.covariance_matrix(n=8, phi=0.7, sigma=1.5)
        np.testing.assert_allclose(R, R.T)

    def test_positive_semidefinite(self):
        """All eigenvalues of the covariance matrix must be >= 0."""
        sf = ShadowingFading(tau=5, N=10)
        R = sf.covariance_matrix(n=10, phi=0.8, sigma=1.0)
        eigvals = np.linalg.eigvalsh(R)
        self.assertTrue(np.all(eigvals >= -1e-10))


class TestJointPDF(unittest.TestCase):
    """Validate the joint PDF of the AR(1) process."""

    def test_pdf_positive(self):
        sf = ShadowingFading(tau=5, N=10)
        np.random.seed(42)
        s = sf.generate_ar1(sigma=1.0)
        pdf_val = sf.joint_pdf(s)
        self.assertGreater(pdf_val, 0.0)

    def test_pdf_independent_case(self):
        """phi=0 => product of marginals."""
        sf = ShadowingFading(tau=0, N=5)
        np.random.seed(42)
        s = sf.generate_ar1(sigma=1.0)
        pdf_val = sf.joint_pdf(s, sigma=1.0, phi=0.0)
        expected = float(np.prod(
            np.exp(-0.5 * s ** 2) / np.sqrt(2 * np.pi)
        ))
        self.assertAlmostEqual(pdf_val, expected, places=6)


class TestSFLOSCalc(unittest.TestCase):
    """Validate the main SF_LOS_calc convenience method."""

    def test_returns_array_of_correct_length(self):
        sf = ShadowingFading(tau=10, N=1000)
        np.random.seed(42)
        samples = sf.SF_LOS_calc(30, "LOS", "SBand")
        self.assertIsInstance(samples, np.ndarray)
        self.assertEqual(len(samples), 1000)

    def test_zero_mean_and_correct_std(self):
        """Mean ~0, std ~ sigma_SF(elevation)."""
        sf = ShadowingFading(tau=10, N=50000)
        np.random.seed(42)
        samples = sf.SF_LOS_calc(30, "LOS", "SBand")
        sigma_ref = float(np.interp(30, _ELEV_GRID, _SIGMA_LOS_S))
        self.assertAlmostEqual(np.mean(samples), 0.0, delta=0.3)
        self.assertAlmostEqual(np.std(samples), sigma_ref, delta=0.5)

    def test_all_finite(self):
        sf = ShadowingFading(tau=15, N=5000)
        np.random.seed(42)
        samples = sf.SF_LOS_calc(45, "NLOS", "KaBand")
        self.assertTrue(np.all(np.isfinite(samples)))

    def test_kaband_higher_sigma(self):
        """Ka-band NLoS should have higher sigma_SF than S-band NLoS."""
        sf = ShadowingFading(tau=10, N=10)
        sigma_s = sf.sigma_sf(30, "NLOS", "SBand")
        sigma_ka = sf.sigma_sf(30, "NLOS", "KaBand")
        self.assertGreater(sigma_ka, sigma_s)

    def test_nlos_higher_sigma_than_los(self):
        """NLoS sigma_SF should be higher than LoS at the same elevation."""
        sf = ShadowingFading(tau=10, N=10)
        for el in [20, 40, 60, 80]:
            with self.subTest(el=el):
                sigma_los = sf.sigma_sf(el, "LOS", "SBand")
                sigma_nlos = sf.sigma_sf(el, "NLOS", "SBand")
                self.assertGreater(sigma_nlos, sigma_los)


class TestReproducibility(unittest.TestCase):
    """Verify that the same seed produces the same samples."""

    def test_seed_reproducibility(self):
        sf = ShadowingFading(tau=10, N=1000)
        np.random.seed(123)
        samples_a = sf.SF_LOS_calc(30, "LOS", "SBand")
        np.random.seed(123)
        samples_b = sf.SF_LOS_calc(30, "LOS", "SBand")
        np.testing.assert_array_equal(samples_a, samples_b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
