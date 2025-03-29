import time

import numpy as np
import plotly.graph_objects as go

from constants import ui_constants


def create_general_layout():
    return go.Layout(
        font=dict(
            family=ui_constants.MAIN_FONT,
            size=ui_constants.FONT_SIZE
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                xanchor="center",
                yanchor="top",
                x=1,
                y=0.5,
                showactive=False,
                buttons=[
                    dict(
                        label="►",
                        method="animate",
                        args=[None, {
                            'frame': {'duration': 5, 'redraw': True},
                            'fromcurrent': True,
                            "mode": "immediate",
                            'transition': {'duration': 5}
                        }]
                    ),
                    dict(
                        label="❚❚",
                        method="animate",
                        args=[[None], {
                            'frame': {'duration': 15, 'redraw': False},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }]
                    )
                ]
            )
        ]
    )


def generate_markers_nbody(data: np.ndarray, colors: list):
    return [go.Scatter3d(
        x=[data[0][body]],
        y=[data[1][body]],
        z=[data[2][body]],
        mode='markers',
        marker=dict(
            size=20,  # Размер маркеров
            symbol='circle',  # Тип маркера (круг)
            color=colors[body],
        ),
        name=f'Тело {body + 1}',  # Подписи при наведении
        hoverinfo='name+x+y+z',  # Показываем координаты и текст при наведении
        showlegend=True
    )
        for body in range(data.shape[1])
    ]


def generate_lines_nbody(data: np.ndarray, colors: list):
    return [go.Scatter3d(
        x=data[:, 0, body],
        y=data[:, 1, body],
        z=data[:, 2, body],
        mode='lines',
        line=dict(
            width=10,
            color=colors[body],
        ),
        text=f'Тело {body + 1}',  # Подписи при наведении
        hoverinfo='skip',  # Показываем координаты и текст при наведении
        showlegend=False
    )
    for body in range(data.shape[2])
]

