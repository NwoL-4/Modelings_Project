from typing import Callable

import numpy as np
import streamlit
from numba import njit


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