import numpy as np
import pandas as pd
import scipy.constants as const

from numba import njit, prange

import plotly.graph_objects as go

import streamlit as st
from streamlit_plotly_events import plotly_events
from streamlit_theme import st_theme

import pages.utils
from pages.error_handler import convert_type


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


def collision_check(num_body, body_radius, coordinate):
    collision = []
    for i_body in range(num_body - 1):
        for j_body in range(i_body + 1, num_body):
            delta_rad = coordinate[:, i_body] - coordinate[:, j_body]
            radius = np.sqrt(np.sum(delta_rad ** 2))
            if body_radius[i_body] + body_radius[j_body] >= radius:
                collision.append([i_body + 1, j_body + 1])
    return collision


def plot_scatter(coordinate, radius, colors, progress_bar):
    theme = st_theme()

    fig = go.Figure()

    # size = radius / radius.max() * 20
    size = 20
    # width = size[body] / 10
    width = 5

    progress_bar.progress(0, text='Визуализирование ...')

    for body in range(coordinate.shape[2]):
        fig.add_trace(go.Scatter3d(
            x=[coordinate[0, 0, body]],
            y=[coordinate[0, 1, body]],
            z=[coordinate[0, 2, body]],
            mode='markers',
            marker=dict(
                color=colors[body],
                size=size
            ),
            name=f'{body + 1} тело'
        ))

        fig.add_trace(go.Scatter3d(
            x=[coordinate[0, 0, body]],
            y=[coordinate[0, 1, body]],
            z=[coordinate[0, 2, body]],
            mode='lines',
            line=dict(
                color=colors[body],
                width=width
            ),
            name=f'Траектория {body + 1} тела'
        ))

        progress_bar.progress(body / coordinate.shape[2], text='Визуализирование ...')

    frames = []

    progress_bar.progress(0, text='Визуализирование ...')

    for index in range(coordinate.shape[0]):

        data = []

        for body in range(coordinate.shape[2]):
            data.append(go.Scatter3d(
                x=[coordinate[index, 0, body]],
                y=[coordinate[index, 1, body]],
                z=[coordinate[index, 2, body]],
                mode='markers',
                marker=dict(
                    color=colors[body],
                    size=size
                ),
                name=f'{body + 1} тело'
            ))
            data.append(go.Scatter3d(
                x=coordinate[:index + 1, 0, body],
                y=coordinate[:index + 1, 1, body],
                z=coordinate[:index + 1, 2, body],
                mode='lines',
                line=dict(
                    color=colors[body],
                    width=width
                ),
                name=f'Траектория {body + 1} тела'
            ))

        frames.append(go.Frame(name=str(index),
                               data=data
                               )
                      )

        progress_bar.progress(index / coordinate.shape[0], text='Визуализирование ...')

    steps = []
    for index in range(coordinate.shape[0]):
        step = dict(
            label=str(index),
            method='animate',
            args=[[str(index)]]
        )
        steps.append(step)

    sliders = [dict(
        steps=steps,
    )]

    fig.update_layout(
        plot_bgcolor=theme['backgroundColor'],
        paper_bgcolor=theme['backgroundColor'],
        font=dict(
            family=theme['font'],
            color=theme['textColor'],
        ),
        scene=dict(
            xaxis=dict(
                title=dict(
                    text='X, м'
                )
            ),
            yaxis=dict(
                title=dict(
                    text='Y, м'
                )
            ),
            zaxis=dict(
                title=dict(
                    text='Z, м'
                )
            ),
        ),
        updatemenus=[dict(direction="left",
                          x=1.05,
                          xanchor="center",
                          y=0.5,
                          showactive=False,
                          type="buttons",
                          buttons=[
                              dict(label="►", method="animate", args=[None, {"fromcurrent": True}]),
                              dict(label="❚❚", method="animate",
                                   args=[[None], {"frame": {"duration": 15, "redraw": False},
                                                  "mode": "immediate",
                                                  "transition": {"duration": 15}}])])],
    )

    fig.layout.sliders = sliders
    fig.frames = frames

    plotly_events(fig, click_event=False, override_height=1000, override_width='100%')


def color_body(s):
    return [f'background-color: {color}' for color in s]


def run_n_body():
    col1, col2 = st.columns(2)
    with col1:
        text_sim = 'Параметры симуляции'
        st.write(text_sim)
        with st.form(key='sim'):
            n = st.number_input('Число тел', help='Выберите целое число от 2 до 10',
                                min_value=2, max_value=10)
            time_step = st.text_input('Временной шаг', value="10")
            num_iteration = st.number_input('Число итераций', help='Выберите целое число от 1 до 1ed10',
                                            min_value=1, max_value=int(1e10), value=1000)
            submit_button_sim = st.form_submit_button('Отправить ' + text_sim,
                                                      use_container_width=True)
            if n and submit_button_sim and time_step and num_iteration:
                st.success('Выбраны ' + text_sim)
                st.session_state.num_body = convert_type(n, int)
                st.session_state.time_step = convert_type(time_step, float)
                st.session_state.num_iteration = convert_type(num_iteration, int)
                st.session_state.colors_body = ['#%06X' % np.random.randint(0, 0xFFFFFF) for _ in range(st.session_state.num_body)]

    with col2:
        if 'num_body' in st.session_state:

            text_body = 'Начальные параметры тел'
            st.write(text_body)

            new_dF = pd.DataFrame(data={
                'Номер тела': np.arange(st.session_state.num_body) + 1,
                'Цвет тела': st.session_state.colors_body,
                'Масса, кг': ['0'] * st.session_state.num_body,
                'Радиус, м': ['0'] * st.session_state.num_body,
                'Начальная скорость x, м/c': ['0'] * st.session_state.num_body,
                'Начальная скорость y, м/c': ['0'] * st.session_state.num_body,
                'Начальная скорость z, м/c': ['0'] * st.session_state.num_body,
                'Координата x, м': ['0'] * st.session_state.num_body,
                'Координата y, м': ['0'] * st.session_state.num_body,
                'Координата z, м': ['0'] * st.session_state.num_body,
            })

            with st.form(key='body_param'):
                if 'old_dF' not in st.session_state:
                    new_dF = st.data_editor(new_dF, hide_index=True, disabled=('Номер тела', 'Цвет тела'))
                else:
                    if new_dF.shape == st.session_state.old_dF.shape:
                        new_dF = st.data_editor(st.session_state.old_dF, hide_index=True, disabled=('Номер тела',))

                    else:
                        row = min(new_dF.shape[0], st.session_state.old_dF.shape[0])
                        new_dF.iloc[[np.arange(row)]] = st.session_state.old_dF.iloc[np.arange(row)]

                        new_dF = st.data_editor(new_dF, hide_index=True, disabled=('Номер тела',))
                submit_button_body = st.form_submit_button('Отправить ' + text_body,
                                                           use_container_width=True)
                if submit_button_body:
                    st.session_state.old_dF = new_dF
                    st.session_state.old_dF.style.apply(color_body, axis=1)
                    st.success('Выбраны ' + text_sim)


    if ('num_body' in st.session_state) and ('old_dF' in st.session_state):
        st.write(f'Выбрано {st.session_state.num_body} тела')
        st.write(f'Начальные параметры')
        st.dataframe(st.session_state.old_dF.style.apply(lambda x: color_body(x) if x.name == 'Цвет тела' else [''] * len(x),
                                                         axis=0),
                     hide_index=True)
        try:
            coord_x = np.array(st.session_state.old_dF['Координата x, м'].to_numpy(), dtype=float)
            coord_y = np.array(st.session_state.old_dF['Координата y, м'].to_numpy(), dtype=float)
            coord_z = np.array(st.session_state.old_dF['Координата z, м'].to_numpy(), dtype=float)

            speed_x = np.array(st.session_state.old_dF['Начальная скорость x, м/c'].to_numpy(), dtype=float)
            speed_y = np.array(st.session_state.old_dF['Начальная скорость y, м/c'].to_numpy(), dtype=float)
            speed_z = np.array(st.session_state.old_dF['Начальная скорость z, м/c'].to_numpy(), dtype=float)

            mass_body = np.array(st.session_state.old_dF['Масса, кг'].to_numpy(), dtype=float)
            radius_body = np.array(st.session_state.old_dF['Радиус, м'].to_numpy(), dtype=float)
        except:
            raise ValueError('Введите данные типа float'
                             '\nПример: 1.1e-3  (== 0.0011)')

        data = np.zeros((st.session_state.num_iteration + 1, 2, 3, st.session_state.num_body))
        data[:] = np.nan

        data[0] = np.array([
            [coord_x, coord_y, coord_z],
            [speed_x, speed_y, speed_z]
        ])

        ct = 0

        progress_bar = st.progress(0, text='Моделирование...')
        for i in range(1, st.session_state.num_iteration + 1):
            collisions = collision_check(st.session_state.num_body, radius_body, data[i - 1, 0, :, :])
            if collisions:
                st.write(f'Моделирование завершено досрочно.')
                for collision in collisions:
                    st.write(f'Столкнулись {collision[0]} и {collisions[1]} тела')
                break
            ct += st.session_state.time_step
            data[i] = pages.utils.rk4(ct, st.session_state.time_step, data[i - 1], solve=n_body_solve, func=mass_body)

            progress_bar.progress(i / st.session_state.num_iteration, text='Моделирование...')

        plot_scatter(data[:, 0, :, :], radius_body, st.session_state.old_dF['Цвет тела'].to_numpy(), progress_bar)
        progress_bar.success('Готово')