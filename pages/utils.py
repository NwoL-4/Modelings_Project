from typing import Callable

import numpy as np
from numba import njit, prange


@njit(parallel=True, cache=True)
def rk4(ct: float,
        ts: float,
        data: np.ndarray,
        solve: Callable,
        func = None) -> np.ndarray:

    coordinate = data[0]
    speed = data[1]

    k1, l1 = ts * speed, ts * solve(coordinate, speed, ct, func)
    k2, l2 = ts * (speed + l1 / 2), ts * solve(coordinate + k1 / 2, speed + l1 / 2, ct + ts / 2, func)

    k3, l3 = ts * (speed + l2 / 2), ts * solve(coordinate + k2 / 2, speed + l2 / 2, ct + ts / 2, func)

    k4, l4 = ts * (speed + l3), ts * solve(coordinate + k3, speed + l3, ct + ts, func)

    data = np.zeros_like(data)

    data[0] = coordinate + (k1 + 2 * k2 + 2 * k3 + k4) / 6
    data[1] = speed + (l1 + 2 * l2 + 2 * l3 + l4) / 6

    return data


@njit(cache=True, parallel=True)
def euler_Method(temperature, time_step, alpha, hx, hy):
    new_data = temperature.copy()

    for index_x in prange(1, temperature.shape[0] - 1):
        for index_y in prange(1, temperature.shape[1] - 1):
            new_data[index_x, index_y] = (temperature[index_x, index_y] +
                                          alpha ** 2 * time_step * (
                    (temperature[index_x - 1, index_y] - 2 * temperature[index_x, index_y] + temperature[index_x + 1, index_y]) / (hx ** 2) +
                    (temperature[index_x, index_y - 1] - 2 * temperature[index_x, index_y] + temperature[index_x, index_y + 1]) / (hy ** 2)
            )
            )
    return new_data