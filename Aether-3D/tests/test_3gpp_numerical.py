#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, math, unittest
import numpy as np
from unittest.mock import MagicMock

for _m in ["skyfield", "skyfield.api", "sgp4", "sgp4.api", "sympy", "progress", "progress.bar"]:
    if _m not in sys.modules:
        sys.modules[_m] = MagicMock()

_R = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_R, "..", "3DANTS", "Communication channel"))

from Satellite_comm_param import Satellite_communication_parameter
from Air_objects_class import Air
from RX_power_calc import Rx_power

scp = Satellite_communication_parameter()
rx = Rx_power()
air = Air("Urban", 2.5e9)


class TestSatelliteCommParam3GPP(unittest.TestCase):
    """Exact values from 3GPP TR 38.811 Table 5.1.1-1."""

    def test_s_band_dl_eirp_density(self):
        eirp, *_ = scp.parameters(2.5e9, "S", "DL")
        self.assertEqual(eirp, 34)

    def test_s_band_dl_max_gain(self):
        _, gain, *_ = scp.parameters(2.5e9, "S", "DL")
        self.assertEqual(gain, 30)

    def test_s_band_dl_beamwidth(self):
        _, _, bw, *_ = scp.parameters(2.5e9, "S", "DL")
        self.assertAlmostEqual(bw, 4.4127)

    def test_s_band_dl_beam_diameter(self):
        _, _, _, bd, _ = scp.parameters(2.5e9, "S", "DL")
        self.assertEqual(bd, 50)

    def test_s_band_dl_bandwidth(self):
        *_, bw = scp.parameters(2.5e9, "S", "DL")
        self.assertEqual(bw, 30)

    def test_ka_band_dl_eirp_density(self):
        eirp, *_ = scp.parameters(20e9, "Ka", "DL")
        self.assertEqual(eirp, 40)

    def test_ka_band_dl_max_gain(self):
        _, gain, *_ = scp.parameters(20e9, "Ka", "DL")
        self.assertEqual(gain, 38.5)

    def test_ka_band_dl_beamwidth(self):
        _, _, bw, *_ = scp.parameters(20e9, "Ka", "DL")
        self.assertAlmostEqual(bw, 1.7647)

    def test_ka_band_dl_beam_diameter(self):
        _, _, _, bd, _ = scp.parameters(20e9, "Ka", "DL")
        self.assertEqual(bd, 20)

    def test_ka_band_dl_bandwidth(self):
        *_, bw = scp.parameters(20e9, "Ka", "DL")
        self.assertEqual(bw, 400)

    def test_s_band_ul_g_over_t(self):
        got, _, _ = scp.parameters(2.5e9, "S", "UL")
        self.assertEqual(got, 1.1)

    def test_ka_band_ul_g_over_t(self):
        got, _, _ = scp.parameters(20e9, "Ka", "UL")
        self.assertEqual(got, 13)

    def test_ka_higher_eirp_than_s(self):
        e_s, *_ = scp.parameters(2.5e9, "S", "DL")
        e_ka, *_ = scp.parameters(20e9, "Ka", "DL")
        self.assertGreater(e_ka, e_s)

    def test_ka_narrower_beamwidth(self):
        _, _, bw_s, *_ = scp.parameters(2.5e9, "S", "DL")
        _, _, bw_ka, *_ = scp.parameters(20e9, "Ka", "DL")
        self.assertLess(bw_ka, bw_s)


class TestFSPLNumerical(unittest.TestCase):
    """FSPL = 32.45 + 20*log10(d_m) + 20*log10(f_GHz)."""

    def test_fspl_known(self):
        self.assertAlmostEqual(float(rx.FSPl_only(2.5e9, 100)), 140.41, delta=0.1)

    def test_fspl_10x_dist(self):
        f1 = float(rx.FSPl_only(2.5e9, 10))
        f2 = float(rx.FSPl_only(2.5e9, 100))
        self.assertAlmostEqual(f2 - f1, 20.0, delta=0.1)

    def test_fspl_10x_freq(self):
        f1 = float(rx.FSPl_only(2.5e9, 100))
        f2 = float(rx.FSPl_only(25e9, 100))
        self.assertAlmostEqual(f2 - f1, 20.0, delta=0.1)

    def test_fspl_consistency(self):
        d = 100000.0; f = 2.5e9
        s = 32.45 + 20*math.log10(d) + 20*math.log10(f/1e9)
        e = 20*math.log10(4*math.pi*d*f/3e8)
        self.assertAlmostEqual(s, e, delta=0.01)


class TestNoisePower3GPP(unittest.TestCase):
    """N = 10*log10(k*T*B*NF_linear)."""

    def test_noise_known(self):
        self.assertAlmostEqual(float(rx.Noise_power_with_NoiseFigure(7.0, 30, 290)), -122.21, delta=0.1)

    def test_noise_bw(self):
        n1 = float(rx.Noise_power_with_NoiseFigure(7.0, 30, 290))
        n2 = float(rx.Noise_power_with_NoiseFigure(7.0, 60, 290))
        self.assertAlmostEqual(n2 - n1, 3.01, delta=0.1)

    def test_noise_nf(self):
        n1 = float(rx.Noise_power_with_NoiseFigure(0.0, 30, 290))
        n2 = float(rx.Noise_power_with_NoiseFigure(10.0, 30, 290))
        self.assertAlmostEqual(n2 - n1, 10.0, delta=0.1)

    def test_noise_no_nf(self):
        r = float(rx.Noise_power_with_NoiseFigure(0.0, 30, 290))
        self.assertAlmostEqual(r, 10*math.log10(1.38e-23 * 290 * 30e6), delta=0.01)


class TestLOSProbability3GPP(unittest.TestCase):
    """Al-Hourani LOS probability."""

    def test_los_urban(self):
        p = float(Air("Urban", 2.5e9).LoS_calculator(45))
        self.assertAlmostEqual(p, 1.0, delta=1e-3)

    def test_los_suburban(self):
        p = float(Air("Suburban", 2.5e9).LoS_calculator(60))
        self.assertAlmostEqual(p, 1.0, delta=1e-3)

    def test_los_in_range(self):
        for env in ["Suburban", "Urban", "DenseUrban"]:
            a = Air(env, 2.5e9)
            for ang in [10, 30, 45, 60, 90]:
                p = float(a.LoS_calculator(ang))
                self.assertGreaterEqual(p, 0.0)
                self.assertLessEqual(p, 1.0 + 1e-9)

    def test_los_increasing(self):
        a = Air("DenseUrban", 2.5e9)
        self.assertGreaterEqual(float(a.LoS_calculator(90)), float(a.LoS_calculator(10)))


class TestGeneralPathLoss3GPP(unittest.TestCase):
    """PL = 20*log10(d_m) + 20*log10(f_Hz) + 20*log10(4*pi/c) + eta."""

    def test_pathloss_known(self):
        gs = np.array([[0.0, 0.0, 0.0]])
        uav = np.array([[2.0, 0.0, 0.0]])
        pl, _ = air.general_pathloss_calculator(gs, uav)
        self.assertAlmostEqual(float(pl), 107.42, delta=0.1)

    def test_nlos_greater(self):
        gs = np.array([[0.0, 0.0, 0.0]])
        uav = np.array([[2.0, 0.0, 0.0]])
        pl_los, pl_nlos = air.general_pathloss_calculator(gs, uav)
        self.assertGreater(float(pl_nlos), float(pl_los))

    def test_eta_diff(self):
        gs = np.array([[0.0, 0.0, 0.0]])
        uav = np.array([[2.0, 0.0, 0.0]])
        pl_los, pl_nlos = air.general_pathloss_calculator(gs, uav)
        self.assertAlmostEqual(float(pl_nlos) - float(pl_los), 19.0, delta=0.1)

    def test_pathloss_dist(self):
        gs = np.array([[0.0, 0.0, 0.0]])
        pl_near, _ = air.general_pathloss_calculator(gs, np.array([[1.0, 0.0, 0.0]]))
        pl_far, _ = air.general_pathloss_calculator(gs, np.array([[5.0, 0.0, 0.0]]))
        self.assertGreater(float(pl_far), float(pl_near))


class TestRicianKFactor3GPP(unittest.TestCase):
    """Air-to-air K-factor: K = rho^2 / (2*sigma^2)."""

    def test_k_known(self):
        k = air.air2air_K_calculator(h1=100.0, h2=200.0, rho_direct=0.5)
        self.assertAlmostEqual(float(k), 0.0743, delta=0.001)

    def test_k_rho(self):
        k1 = air.air2air_K_calculator(100.0, 200.0, 0.5)
        k2 = air.air2air_K_calculator(100.0, 200.0, 2.0)
        self.assertGreater(float(k2), float(k1))

    def test_k_positive(self):
        k = air.air2air_K_calculator(100.0, 200.0, 0.5)
        self.assertGreater(float(k), 0)

    def test_rician_factor_positive(self):
        np.random.seed(42)
        r = air.Rician_factor_calculator(45, -10, 10)
        self.assertGreater(float(np.asarray(r).ravel()[0]), 0)
        self.assertTrue(np.isfinite(float(np.asarray(r).ravel()[0])))


class TestAtmosphericAttenuation(unittest.TestCase):
    """PL_At = 10*log10(10^(A_z/10) / sin(elevation_rad))."""

    def test_atmos_known(self):
        self.assertAlmostEqual(float(rx.atmospheric_att(1.0, 30)), 4.01, delta=0.01)

    def test_atmos_increases(self):
        self.assertGreater(float(rx.atmospheric_att(2.0, 30)), float(rx.atmospheric_att(1.0, 30)))

    def test_atmos_decreases(self):
        self.assertGreater(float(rx.atmospheric_att(1.0, 10)), float(rx.atmospheric_att(1.0, 60)))


class TestAntennaGain(unittest.TestCase):
    """Antenna gain pattern at broadside and off-broadside."""

    def test_gain_broadside(self):
        self.assertEqual(float(rx.antenna_gain_calc(0)), 0.0)

    def test_gain_small_angle(self):
        g = float(rx.antenna_gain_calc(1))
        self.assertGreater(g, 25.0)
        self.assertLess(g, 35.0)

    def test_gain_finite(self):
        self.assertTrue(np.isfinite(float(rx.antenna_gain_calc(3))))


class TestRxLOSProbabilityTable(unittest.TestCase):
    """3GPP TR 38.811 LOS probability table, polynomial fit."""

    ELEV = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    DV = [28.2, 33.1, 39.8, 46.8, 53.7, 61.2, 73.8, 82.0, 98.1]
    UV = [24.6, 38.6, 49.3, 61.3, 72.6, 80.5, 91.9, 96.8, 99.2]
    SV = [78.2, 86.9, 91.9, 92.9, 93.5, 94.0, 94.9, 95.2, 99.8]

    def test_los_dense_urban(self):
        for e, exp in zip(self.ELEV, self.DV):
            self.assertAlmostEqual(float(np.asarray(rx.LOS_prob_calc(e, "Dense_Urban")).ravel()[0]), exp, delta=2.0)

    def test_los_urban(self):
        for e, exp in zip(self.ELEV, self.UV):
            self.assertAlmostEqual(float(np.asarray(rx.LOS_prob_calc(e, "Urban")).ravel()[0]), exp, delta=2.0)

    def test_los_suburban(self):
        for e, exp in zip(self.ELEV, self.SV):
            self.assertAlmostEqual(float(np.asarray(rx.LOS_prob_calc(e, "Sub_Urban")).ravel()[0]), exp, delta=2.0)

    def test_los_interpolated(self):
        v = float(np.asarray(rx.LOS_prob_calc(15, "Urban")).ravel()[0])
        self.assertGreater(v, 0)
        self.assertLess(v, 100)


class TestShadowFadingTable(unittest.TestCase):
    """3GPP TR 38.811 shadow fading tables."""

    ELEV = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    KACL = [29.5, 24.6, 21.9, 20.0, 18.7, 17.8, 17.2, 16.9, 16.8]
    SACL = [19.52, 18.17, 18.42, 18.28, 18.63, 17.68, 16.50, 16.30, 16.30]

    def test_sf_ka_cl(self):
        for e, exp in zip(self.ELEV, self.KACL):
            _, _, cl = rx.SF_LOS_calc(e, "NLOS", "KaBand")
            self.assertAlmostEqual(float(cl), exp, delta=0.01)

    def test_sf_sband_cl(self):
        for e, exp in zip(self.ELEV, self.SACL):
            _, _, cl = rx.SF_LOS_calc(e, "NLOS", "SBand")
            self.assertAlmostEqual(float(cl), exp, delta=0.01)

    def test_sf_los_zero_nlos(self):
        np.random.seed(42)
        _, sn, cl = rx.SF_LOS_calc(30, "LOS", "KaBand")
        self.assertEqual(float(sn), 0.0)
        self.assertEqual(float(cl), 0.0)

    def test_sf_nlos_zero_los(self):
        np.random.seed(42)
        sl, _, _ = rx.SF_LOS_calc(30, "NLOS", "KaBand")
        self.assertEqual(float(sl), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

