#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Large-scale (shadow) fading model for Non-Terrestrial Network (NTN) channels.

This module implements the AR(1) temporal-correlation model for shadow
fading as described in 3GPP TR 38.811.  In NTNs, non-terrestrial nodes
follow predictable overflight trajectories over static ground obstacles,
so the dominant large-scale variation comes from the gradual change of
the elevation angle theta_el rather than from spatial correlation.

The shadow fading S(t) is expressed in decibels as a zero-mean Gaussian
random process:

    s(t) ~ N(0, sigma_SF^2(theta_el, f_c, LoS/NLoS))

where the standard deviation sigma_SF is tabulated in 3GPP TR 38.811
as a function of elevation angle, carrier frequency, environment type
and LoS/NLoS condition.

Temporal correlation
---------------------
Consecutive fading samples are linked via a first-order autoregressive
(AR(1)) process whose exponential autocorrelation function is:

    rho(l) = phi^|l| = exp(-|l| / tau_s)

where phi = exp(-1/tau_s) is the per-TTI correlation coefficient and
tau_s > 0 is the correlation time measured in TTIs (the number of time
slots for the elevation angle to change by approximately 1 degree).

The closed-form AR(1) sequence generator is:

    s_l = phi^l * s_0 + sqrt(1 - phi^2) * sum_{m=1}^{l} g_m * phi^{l-m}

which is equivalent to the recursive form:

    s_0 ~ N(0, sigma^2)
    s_l = phi * s_{l-1} + sqrt(1 - phi^2) * g_l,   g_l ~ N(0, sigma^2)

References
----------
1. 3GPP TR 38.811 (Release 15), "Study on frequency for Non-Terrestrial
   Networks".
2. Matic, P. et al., "Spatial consistency modeling for the shadow
   fading process in mobile radio channels," IEEE Trans. Veh. Tech., 2019.
"""

import numpy as np


# =============================================================================
#  3GPP TR 38.811 shadow-fading sigma_SF lookup tables  [dB]
#  Rows correspond to elevation angles in _ELEVATION_GRID (degrees).
#  S-band ~= 2 GHz,  Ka-band ~= 20 GHz.
# =============================================================================

#: Elevation-angle grid [degrees]
_ELEVATION_GRID = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0])

#: sigma_SF for LoS, S-band [dB]
_SIGMA_LOS_S = np.array([1.79, 1.14, 1.14, 0.92, 1.42, 1.56, 0.85, 0.72, 0.72])

#: sigma_SF for NLoS, S-band [dB]
_SIGMA_NLOS_S = np.array([8.93, 9.08, 8.78, 10.25, 10.56, 10.74, 10.17, 11.52, 11.52])

#: sigma_SF for LoS, Ka-band [dB]
_SIGMA_LOS_KA = np.array([1.9, 1.6, 1.9, 2.3, 2.7, 3.1, 3.0, 3.6, 0.4])

#: sigma_SF for NLoS, Ka-band [dB]
_SIGMA_NLOS_KA = np.array([10.7, 10.0, 11.2, 11.6, 11.8, 10.8, 10.8, 10.8, 10.8])

#: Clutter loss for NLoS, S-band [dB]
_CL_NLOS_S = np.array([19.52, 18.17, 18.42, 18.28, 18.63, 17.68, 16.50, 16.30, 16.30])

#: Clutter loss for NLoS, Ka-band [dB]
_CL_NLOS_KA = np.array([29.5, 24.6, 21.9, 20.0, 18.7, 17.8, 17.2, 16.9, 16.8])


def _clamp_elevation(angle):
    """Clamp elevation angle to the valid 3GPP lookup range [10, 90] degrees."""
    return max(10.0, min(90.0, float(angle)))


class ShadowingFading:
    """
    AR(1) temporally correlated large-scale shadow fading generator.

    The shadow fading process s(t) is a zero-mean Gaussian process in
    decibels with standard deviation sigma_SF(theta_el, f_c, LoS/NLoS)
    taken from the 3GPP TR 38.811 tables.  Temporal correlation is imposed
    via a first-order autoregressive (AR(1)) process::

        s_0 ~ N(0, sigma^2)
        s_l = phi * s_{l-1} + sqrt(1 - phi^2) * g_l,   g_l ~ N(0, sigma^2)

    where phi = exp(-1/tau_s).

    Parameters
    ----------
    tau : float
        Correlation time tau_s in TTIs.  Larger tau_s -> stronger temporal
        correlation.  For LEO satellites, tau_s is typically a few TTIs
        per degree of elevation change; for quasi-stationary nodes
        (GEO, HAPS) it is larger.
    N : int
        Number of fading samples generated per batch.
    """

    def __init__(self, tau, N):
        self.tau = tau
        self.N = N

        # AR(1) correlation coefficient per TTI: phi = exp(-1/tau_s).
        # tau_s -> infinity  =>  phi -> 1  (fully correlated / flat fading)
        # tau_s -> 0         =>  phi -> 0  (uncorrelated)
        if tau > 0:
            self.phi = np.exp(-1.0 / tau)
        else:
            self.phi = 0.0

        # Store lookup tables for sigma_SF and clutter loss
        self._elevation_grid = _ELEVATION_GRID
        self._sigma_los_S = _SIGMA_LOS_S
        self._sigma_nlos_S = _SIGMA_NLOS_S
        self._sigma_los_Ka = _SIGMA_LOS_KA
        self._sigma_nlos_Ka = _SIGMA_NLOS_KA
        self._cl_nlos_S = _CL_NLOS_S
        self._cl_nlos_Ka = _CL_NLOS_KA

    # ------------------------------------------------------------------
    #  API: sigma_SF lookup
    # ------------------------------------------------------------------
    def sigma_sf(self, elevation_angle, scenario, freq_band):
        """Interpolate sigma_SF [dB] from the 3GPP TR 38.811 lookup tables.

        Parameters
        ----------
        elevation_angle : float
            Elevation angle in degrees.
        scenario : str
            LOS or NLOS.
        freq_band : str
            SBand or KaBand.

        Returns
        -------
        float
            Shadow-fading standard deviation sigma_SF in dB.
        """
        el = _clamp_elevation(elevation_angle)

        if freq_band == "KaBand":
            sigma_table = self._sigma_los_Ka if scenario == "LOS" else self._sigma_nlos_Ka
        else:
            sigma_table = self._sigma_los_S if scenario == "LOS" else self._sigma_nlos_S

        return float(np.interp(el, self._elevation_grid, sigma_table))

    def clutter_loss(self, elevation_angle, freq_band):
        """Clutter loss [dB] for NLoS from 3GPP TR 38.811.

        Parameters
        ----------
        elevation_angle : float
            Elevation angle in degrees.
        freq_band : str
            SBand or KaBand.

        Returns
        -------
        float
            Clutter loss in dB.
        """
        el = _clamp_elevation(elevation_angle)
        cl_table = self._cl_nlos_Ka if freq_band == "KaBand" else self._cl_nlos_S
        return float(np.interp(el, self._elevation_grid, cl_table))

    # ------------------------------------------------------------------
    #  API: AR(1) core generator
    # ------------------------------------------------------------------
    def generate_ar1(self, sigma, phi=None, n=None):
        """Generate an AR(1) correlated zero-mean Gaussian sequence.

        The recursion is:

            s_0 ~ N(0, sigma^2)
            s_l = phi * s_{l-1} + sqrt(1 - phi^2) * g_l

        where g_l ~ N(0, sigma^2) are i.i.d.

        Parameters
        ----------
        sigma : float
            Marginal standard deviation.
        phi : float, optional
            AR(1) coefficient.  Defaults to self.phi.
        n : int, optional
            Number of samples.  Defaults to self.N.

        Returns
        -------
        np.ndarray
            1-D array of n correlated samples.
        """
        if phi is None:
            phi = self.phi
        if n is None:
            n = self.N

        # i.i.d. Gaussian innovations
        g = np.random.normal(0.0, sigma, n)

        # Recursive AR(1) -- O(n) loop.
        # The recursive form is numerically stable and memory-light.
        s = np.empty(n)
        s[0] = g[0]
        sqrt_term = np.sqrt(1.0 - phi ** 2)
        for l in range(1, n):
            s[l] = phi * s[l - 1] + sqrt_term * g[l]
        return s

    # ------------------------------------------------------------------
    #  API: joint distribution utilities
    # ------------------------------------------------------------------
    def covariance_matrix(self, n=None, phi=None, sigma=None):
        """Compute the AR(1) covariance matrix R_s.

        [R_s]_{m,n} = phi^|m-n| * sigma^2

        Parameters
        ----------
        n : int, optional
            Matrix dimension.  Defaults to self.N.
        phi : float, optional
            Correlation coefficient.  Defaults to self.phi.
        sigma : float, optional
            Marginal std dev.  Defaults to 1.0.

        Returns
        -------
        np.ndarray
            n x n covariance matrix.
        """
        if n is None:
            n = self.N
        if phi is None:
            phi = self.phi
        if sigma is None:
            sigma = 1.0

        indices = np.arange(n)
        dist = np.abs(np.subtract.outer(indices, indices))
        return sigma ** 2 * phi ** dist

    def joint_pdf(self, s, sigma=None, phi=None):
        """Evaluate the joint PDF of an AR(1) sequence.

        p_s(s) = 1/sqrt((2*pi)^L * det(R_s)) * exp(-1/2 * s^T * R_s^-1 * s)

        Parameters
        ----------
        s : np.ndarray
            Sequence of length n.
        sigma : float, optional
            Marginal std dev.  Defaults to 1.0.
        phi : float, optional
            Correlation coefficient.  Defaults to self.phi.

        Returns
        -------
        float
            Joint probability density.
        """
        if sigma is None:
            sigma = 1.0
        if phi is None:
            phi = self.phi

        n = len(s)
        R = self.covariance_matrix(n, phi, sigma)
        det_R = np.linalg.det(R)

        # Degenerate case (phi^|m-n| -> 0 => independent)
        if det_R == 0:
            return float(np.prod(
                np.exp(-0.5 * (s / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
            ))

        inv_R = np.linalg.inv(R)
        exponent = -0.5 * s @ inv_R @ s
        norm_const = 1.0 / np.sqrt((2 * np.pi) ** n * det_R)
        return float(norm_const * np.exp(exponent))

    # ------------------------------------------------------------------
    #  API: main entry point -- matches the original method signature
    # ------------------------------------------------------------------
    def SF_LOS_calc(self, elevation_angle, scenario, freq_band):
        """Generate a batch of temporally correlated shadow-fading samples.

        Convenience wrapper around sigma_sf and generate_ar1.

        Parameters
        ----------
        elevation_angle : float
            Elevation angle in degrees [10, 90].
        scenario : str
            LOS or NLOS.
        freq_band : str
            SBand or KaBand.

        Returns
        -------
        np.ndarray
            1-D array of self.N shadow-fading samples in dB.
        """
        sigma = self.sigma_sf(elevation_angle, scenario, freq_band)
        return self.generate_ar1(sigma)
