#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file was created by the Department of Communications Engineering,
University of Bremen, Germany.
https://github.com/ant-uni-bremen
Copyright (c) 2026 Department of Communications Engineering, University of Bremen
SPDX-License-Identifier: Apache-2.0
"""

import numpy as np
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def generate_sphere_points(num_points=1, radius=5.0, center=(0, 0, 0)):
    """Generate uniformly distributed points on a sphere surface.

    Uses the inverse-CDF method: theta ~ U(0, 2*pi),
    phi = acos(1 - 2*u) where u ~ U(0, 1), which gives
    a uniform distribution on the sphere.
    """
    x_center, y_center, z_center = center
    x_values, y_values, z_values = [], [], []
    for _ in range(num_points):
        theta = 2 * math.pi * np.random.uniform()
        phi = math.acos(1 - 2 * np.random.uniform())
        x = radius * math.sin(phi) * math.cos(theta) + x_center
        y = radius * math.sin(phi) * math.sin(theta) + y_center
        z = radius * math.cos(phi) + z_center
        x_values.append(x)
        y_values.append(y)
        z_values.append(z)
    return np.array(x_values), np.array(y_values), np.array(z_values)


if __name__ == '__main__':
    # Set up random number generator with system time as seed
    np.random.seed(None)

    # Generate points
    xv, yv, zv = generate_sphere_points(num_points=1, radius=5.0, center=(0, 0, 0))

    # Plot the points
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(0, 0, 0, s=5, c='red', marker='o')
    ax.scatter(xv, yv, zv, s=5, c='blue', marker='o')

    # Set labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    # Show the plot
    plt.show()
