from typing import Callable

import numpy as np
from PySide6.QtCore import *
from numba import njit, prange
from scipy import constants as const


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, index=QModelIndex):
        return self._data.shape[0]

    def columnCount(self, parnet=QModelIndex):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                value = self._data.iloc[index.row(), index.column()]
                return str(value)

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._data.columns[col]

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEditable
        if index.column() in [0, 1]:
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable


def collision_check(num_body, body_radius, coordinate):
    collision = []
    for i_body in range(num_body - 1):
        for j_body in range(i_body + 1, num_body):
            delta_rad = coordinate[:, i_body] - coordinate[:, j_body]
            radius = np.sqrt(np.sum(delta_rad ** 2))
            if body_radius[i_body] + body_radius[j_body] >= radius:
                collision.append([i_body + 1, j_body + 1])
    return collision

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


@njit(parallel=True, cache=True)
def n_body_solve(coordinate, speed, ct, masses):
    tensor_force = np.zeros((3, coordinate.shape[1], coordinate.shape[1]))

    for index_i in prange(coordinate.shape[1] - 1):
        for index_j in prange(index_i + 1, coordinate.shape[1]):
            coord_i = coordinate[:, index_i]
            coord_j = coordinate[:, index_j]

            delta_radius = coord_i - coord_j
            radius = np.sqrt(np.sum(delta_radius ** 2))
            tensor_force[:, index_i, index_j] = - (const.G * masses[index_i] * masses[index_j] /
                                                   (radius ** 3)) * delta_radius
            tensor_force[:, index_j, index_i] = -tensor_force[:, index_i, index_j]
    force = np.sum(tensor_force, axis=2)
    return force / masses