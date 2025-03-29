import numpy as np
import pandas as pd

def create_dataframe_Nbody(num_body: int, color_body: list):

    return pd.DataFrame({
        'Номер тела': np.arange(1, num_body + 1, 1),
        'Цвет тела': color_body[:num_body],
        'Масса, кг': ['1e13'] * num_body,
        'Радиус, м': ['1'] * num_body,
        # 'Начальная скорость x, м/c': ['0'] * num_body,
        # 'Начальная скорость y, м/c': ['0'] * num_body,
        # 'Начальная скорость z, м/c': ['0'] * num_body,
        'Начальная скорость x, м/c': [0, 0, 2],
        'Начальная скорость y, м/c': [2, 0, 0],
        'Начальная скорость z, м/c': [0, 2, 0],
        # 'Координата x, м': ['0'] * num_body,
        # 'Координата y, м': ['0'] * num_body,
        # 'Координата z, м': ['0'] * num_body,
        'Координата x, м': [100, 0, 0],
        'Координата y, м': [0, 100, 0],
        'Координата z, м': [0, 0, 100],
    })


def collision_check(num_body, body_radius, coordinate):
    collision = []
    for i_body in range(num_body - 1):
        for j_body in range(i_body + 1, num_body):
            delta_rad = coordinate[:, i_body] - coordinate[:, j_body]
            radius = np.sqrt(np.sum(delta_rad ** 2))
            if body_radius[i_body] + body_radius[j_body] >= radius:
                collision.append([i_body + 1, j_body + 1])
    return collision if collision != [] else False