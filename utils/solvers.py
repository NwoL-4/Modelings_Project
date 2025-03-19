import numpy as np
from numba import njit, prange

from constants import physics_constants


@njit(parallel=True, cache=True)
def n_body_solve(coordinate, speed, ct, masses):
    tensor_force = np.zeros((3, coordinate.shape[1], coordinate.shape[1]))

    for index_i in prange(coordinate.shape[1] - 1):
        for index_j in prange(index_i + 1, coordinate.shape[1]):
            coord_i = coordinate[:, index_i]
            coord_j = coordinate[:, index_j]

            delta_radius = coord_i - coord_j
            radius = np.sqrt(np.sum(delta_radius ** 2))
            tensor_force[:, index_i, index_j] = - (physics_constants.GRAVITATION_CONSTANT * masses[index_i] * masses[index_j] /
                                                   (radius ** 3)) * delta_radius
            tensor_force[:, index_j, index_i] = -tensor_force[:, index_i, index_j]
    force = np.sum(tensor_force, axis=2)
    return force / masses


def pend_solve(angle, speed, ct, lenghtPend):
    return - physics_constants.GRAVITATION_CONSTANT / lenghtPend * np.sin(angle)
