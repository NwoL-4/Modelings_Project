import time
from itertools import product

import numpy as np
import pandas as pd
import scipy.constants as const
import select

from numba import njit, prange

import plotly.graph_objects as go

import streamlit as st
from streamlit_plotly_events import plotly_events
from streamlit_theme import st_theme

import pages.utils
from pages.error_handler import convert_type
from pages.utils import euler_Method

positiveInt = 'Выберите положительное целое число'
positiveFloat = 'Выберите положительное число'
text_sim = 'Параметры симуляции'
text_plate = 'Параметры тела'
text_conditions = 'Начальные и Граничные условия'
condition_percent = 'Выберите число от 0 до 100'
center_data = """
    <style>
        .box {
            text-align: center;
            vertical-alignL: middle;
            }
    </style>"""
justify_data = """
    <style>
        .box {
            text-align: justify;
            vertical-alignL: middle;
            }
    </style>"""


def plot_heat_eq(x_range, y_range, temperature, theme, progress_bar, num_view):
    fig = go.Figure()

    color_slice = 20
    max_temp = np.max(temperature)
    min_temp = np.min(temperature)

    step = temperature.shape[0] // num_view
    indexes_range = range(0, temperature.shape[0], step)

    fig.add_trace(go.Contour(
        x=x_range,
        y=y_range,
        z=temperature[0],
        colorbar=dict(
            thickness=30,
            thicknessmode='pixels',
            len=1.3,
            lenmode='fraction',
            outlinewidth=1
        ),
        contours=dict(
            coloring='heatmap',
            start=min_temp,
            end=max_temp,
            size=(max_temp - min_temp) / color_slice
        )
    ))

    frames = []
    for index in indexes_range:
        frames.append(
            go.Frame(name=str(index), data=[
                go.Contour(
                    x=x_range,
                    y=y_range,
                    z=temperature[index],
                    colorbar=dict(
                        thickness=30,
                        thicknessmode='pixels',
                        len=1.3,
                        lenmode='fraction',
                        outlinewidth=1
                    ),
                    contours=dict(
                        coloring='heatmap',
                        start=min_temp,
                        end=max_temp,
                        size=(max_temp - min_temp) / color_slice
                    )
                )
            ])
        )
        progress_bar.progress((index + 1) / temperature.shape[0], text='Загрузка фреймов ...')

    steps = []
    for index in indexes_range:
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
        xaxis=dict(
            range=[0, x_range[-1]],
            title=dict(
                text='X, м'
            )
            ),
        yaxis=dict(
            range=[0, y_range[-1]],
            title=dict(
                text='Y, м'
            )
        ),
        updatemenus=[dict(direction="left",
                          x=0.5,
                          xanchor="center",
                          y=-0.2,
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

    progress_bar.success('Загрузка завершена')
    plotly_events(fig, click_event=False)


def get_temp_source(a, b, a_source_perc, b_source_perc, r_source, num_nodes, temp, temp_source):
    new_temp = temp.copy()
    a_range = np.linspace(0, a, num=num_nodes)
    b_range = np.linspace(0, b, num=num_nodes)
    for x, y in product(range(a_range.shape[0]), range(b_range.shape[0])):
        if ((a_range[x] - a_source_perc * a) ** 2 +
                (b_range[y] - b_source_perc * b) ** 2
                <= r_source ** 2):
            new_temp[x, y] = temp_source
    return new_temp


def run_heat_equation():
    theme = st_theme()

    col1, col2 = st.columns(2)
    text = st.empty()
    text.subheader(text_conditions)

    col1.subheader(text_sim)
    col2.subheader(text_plate)

    with col1:
        sim = st.form(key='sim')
    with col2:
        plate_param = st.form(key='plate_param')

    bound_type = st.form(key='bound-type')
    init_value = st.form(key='init-value')

    writer = st.empty()

    ########################################################################################################################
    # Параметры симуляции
    with sim:
        n = st.number_input('Число узлов вдоль каждой оси', help=positiveInt,
                            min_value=2, max_value=1000, value=100, key='n')
        t = st.text_input('Число фреймов для просчета', value='10', help=positiveInt, key='t')
        num_view = st.number_input('Число фреймов для отображения',
                                   min_value=2, max_value=500, value="min", help=positiveInt)
        use_source = st.toggle('Использовать источник?')

        submit_button_sim = st.form_submit_button('Отправить ' + text_sim,
                                                  use_container_width=True)

        if n and t and num_view and submit_button_sim:
            st.session_state.num_nodes = convert_type(n, int)
            st.session_state.time = convert_type(t, float)
            st.session_state.time = convert_type(st.session_state.time, int)
            st.session_state.num_view = convert_type(num_view, int)
            st.session_state.use_source = use_source
            writer.success(f'Выбраны {text_sim}')
    ########################################################################################################################
    # Параметры пластины
    if 'num_nodes' in st.session_state:
        with plate_param:
            a = st.text_input('Размер пластины вдоль x, м',
                              help=positiveFloat,
                              value='0.1', key='ax')
            b = st.text_input('Размер пластины вдоль y, м',
                              help=positiveFloat,
                              value='0.1', key='by')
            alpha = st.text_input('Коэффициент теплопроводности, м^2/c',
                                  help=positiveFloat,
                                  value='1.11e-4', key='alpha_coeff')
            if st.session_state.use_source:
                power_source = st.text_input('Мощность источника, Вт',
                                             help=positiveFloat,
                                             value='1', key='vps')
                radius_source = st.text_input('Радиус источника, м',
                                              help=positiveFloat,
                                              value='1e-2', key='vrs')
                percent_a = st.text_input(
                    'Расположение источника по оси x (в процентах от размера пластины вдоль x), %',
                    help=condition_percent,
                    value='50', key='percent-a')
                percent_b = st.text_input(
                    'Расположение источника по оси y (в процентах от размера пластины вдоль y), %',
                    help=condition_percent,
                    value='50', key='percent-b')

            submit_button_plate = st.form_submit_button('Отправить ' + text_plate,
                                                        use_container_width=True)
            if a and b and alpha and submit_button_plate:
                st.session_state.a = convert_type(a, float)
                st.session_state.b = convert_type(b, float)
                st.session_state.alpha = convert_type(alpha, float)
                if st.session_state.use_source:
                    if power_source and radius_source and percent_a and percent_b:
                        st.session_state.power_source = convert_type(power_source, float)
                        st.session_state.radius_source = convert_type(radius_source, float)
                        st.session_state.percent_a = convert_type(percent_a, float)
                        st.session_state.percent_b = convert_type(percent_b, float)
                writer.success(f'Выбраны {text_plate}')
    ########################################################################################################################
    # Начальные и граничные условия
    if 'alpha' in st.session_state:
        with bound_type:
            col1, col2 = st.columns(2)
            with col1:
                boundary_type = st.radio('Тип граничные условий',
                                         ['Температура одинакова на всех границах',
                                          'Различная температура на границах',
                                          'Различные температуры на углах'],
                                         index=0, horizontal=True)
            with col2:
                st.markdown(center_data, unsafe_allow_html=True)
                submit_button_type = st.form_submit_button('Отправить тип ГУ')
            if boundary_type and submit_button_type:
                st.session_state.boundary_type = boundary_type
                writer.success(f'Выбран тип ГУ')
    if 'boundary_type' in st.session_state:
        with init_value:
            init_temp = st.text_input('Начальная температура, К',
                                      help=positiveFloat,
                                      value='300', key='init-temp')
            match boundary_type:
                case 'Температура одинакова на всех границах':
                    boundary_temp = st.text_input('Температура границы, К',
                                                  help=positiveFloat,
                                                  value='273', key='boundary-temp')
                case 'Различная температура на границах':
                    col1, col2, col3 = st.columns(3)
                    with col2:
                        upBond_temp = st.text_input('Температура верхней границы, К',
                                                    help=positiveFloat,
                                                    value='273', key='upBond-temp')
                        downBond_temp = st.text_input('Температура нижней границы, К',
                                                      help=positiveFloat,
                                                      value='273', key='downBond-temp')
                    with col1:
                        st.markdown(justify_data, unsafe_allow_html=True)
                        leftBond_temp = st.text_input('Температура левой границы, К',
                                                      help=positiveFloat,
                                                      value='273', key='leftBond-temp')
                    with col3:
                        st.markdown(justify_data, unsafe_allow_html=True)
                        rightBond_temp = st.text_input('Температура верхней границы, К',
                                                       help=positiveFloat,
                                                       value='273', key='rightBond-temp')
                case 'Различные температуры на углах':
                    col1, col2 = st.columns(2)
                    with col1:
                        ul_temp = st.text_input('Температура верхнего левого угла, К',
                                                help=positiveFloat,
                                                value='273', key='ul-temp')
                        dl_temp = st.text_input('Температура нижнего левого угла, К',
                                                help=positiveFloat,
                                                value='273', key='dl-temp')
                    with col2:
                        ur_temp = st.text_input('Температура верхнего правого угла, К',
                                                help=positiveFloat,
                                                value='273', key='ur-temp')
                        dr_temp = st.text_input('Температура нижнего правого угла, К',
                                                help=positiveFloat,
                                                value='273', key='dr-temp')
            submit_button_condition = st.form_submit_button('Отправить ' + text_conditions,
                                                            use_container_width=True)
            match boundary_type:
                case 'Температура одинакова на всех границах':
                    if boundary_temp and boundary_type and submit_button_condition:
                        st.session_state.init_temp = convert_type(init_temp, float)
                        st.session_state.boundary_temp = convert_type(boundary_temp, float)
                        writer.success(f'Выбраны {text_conditions}')
                case 'Различная температура на границах':
                    if upBond_temp and downBond_temp and leftBond_temp and rightBond_temp and boundary_type and submit_button_condition:
                        st.session_state.init_temp = convert_type(init_temp, float)
                        st.session_state.upBond_temp = convert_type(upBond_temp, float)
                        st.session_state.downBond_temp = convert_type(downBond_temp, float)
                        st.session_state.leftBond_temp = convert_type(leftBond_temp, float)
                        st.session_state.rightBond_temp = convert_type(rightBond_temp, float)
                        writer.success(f'Выбраны {text_conditions}')
                case 'Различные температуры на углах':
                    if ul_temp and dl_temp and ur_temp and dr_temp and submit_button_condition:
                        st.session_state.ur_temp = convert_type(ur_temp, float)
                        st.session_state.ul_temp = convert_type(ul_temp, float)
                        st.session_state.dr_temp = convert_type(dr_temp, float)
                        st.session_state.dl_temp = convert_type(dl_temp, float)
                        writer.success(f'Выбраны {text_conditions}')
    ########################################################################################################################
    # Создание температурной карты
    if 'init_temp' in st.session_state:
        x_range = np.linspace(0, st.session_state.a, num=st.session_state.num_nodes, endpoint=True)
        y_range = np.linspace(0, st.session_state.b, num=st.session_state.num_nodes, endpoint=True)

        x, y = np.meshgrid(x_range, y_range)

        hx = np.mean(np.diff(x_range))
        hy = np.mean(np.diff(y_range))

        time_step = 1 / 2 * hx * hy

        time_array = np.arange(st.session_state.time) * time_step

        writer.write(f'Будет промоделировано {time_array[-1]} секунд')

        temperature = st.session_state.init_temp * np.ones(shape=(st.session_state.time,
                                                                  st.session_state.num_nodes,
                                                                  st.session_state.num_nodes),
                                                           dtype=float)
        match st.session_state.boundary_type:
            case 'Температура одинакова на всех границах':
                temperature[0, 0, :] = temperature[0, -1, :] = temperature[0, :, 0] = temperature[0, :,
                                                                                      -1] = st.session_state.boundary_temp
            case 'Различная температура на границах':
                temperature[0, :, 0] = st.session_state.leftBond_temp
                temperature[0, :, -1] = st.session_state.rightBond_temp
                temperature[0, 0, :] = st.session_state.downBond_temp
                temperature[0, -1, :] = st.session_state.upBond_temp
                temperature[0, 0, 0] = np.mean([st.session_state.leftBond_temp,
                                                st.session_state.downBond_temp])
                temperature[0, -1, 0] = np.mean([st.session_state.leftBond_temp,
                                                 st.session_state.upBond_temp])
                temperature[0, 0, -1] = np.mean([st.session_state.rightBond_temp,
                                                 st.session_state.downBond_temp])
                temperature[0, -1, -1] = np.mean([st.session_state.rightBond_temp,
                                                  st.session_state.upBond_temp])
            case 'Различные температуры на углах':
                temperature[0, 0, :] = y_range * (
                        st.session_state.dr_temp - st.session_state.dl_temp) / st.session_state.b + st.session_state.dl_temp
                temperature[0, :, 0] = x_range * (
                        st.session_state.ul_temp - st.session_state.dl_temp) / st.session_state.a + st.session_state.dl_temp
                temperature[0, -1, :] = y_range * (
                        st.session_state.ur_temp - st.session_state.ul_temp) / st.session_state.b + st.session_state.ul_temp
                temperature[0, :, -1] = x_range * (
                        st.session_state.ur_temp - st.session_state.dr_temp) / st.session_state.a + st.session_state.dr_temp

        if st.session_state.use_source:
            temp_source = (st.session_state.power_source /
                           (const.Stefan_Boltzmann * np.pi * (st.session_state.radius_source ** 2))) ** (1 / 4)
            temperature[0] = get_temp_source(st.session_state.a,
                                             st.session_state.b,
                                             st.session_state.percent_a * 0.01,
                                             st.session_state.percent_b * 0.01,
                                             st.session_state.radius_source,
                                             st.session_state.num_nodes,
                                             temperature[0],
                                             temp_source)

        writer.success('Создана пластина с НУ и ГУ')

        button_run = st.toggle('Запуск')
        if button_run:

            for index_t in range(1, st.session_state.time):
                temperature[index_t] = euler_Method(temperature[index_t - 1],
                                                    time_step,
                                                    st.session_state.alpha,
                                                    hx, hy)
                if st.session_state.use_source:
                    temperature[index_t] = get_temp_source(st.session_state.a,
                                                           st.session_state.b,
                                                           st.session_state.percent_a * 0.01,
                                                           st.session_state.percent_b * 0.01,
                                                           st.session_state.radius_source,
                                                           st.session_state.num_nodes,
                                                           temperature[index_t - 1],
                                                           temp_source)
                writer.progress(index_t / st.session_state.time, text='Моделирование')

            plot_heat_eq(x_range, y_range, temperature, theme, writer, st.session_state.num_view)

            writer.success('Готово')
            time.sleep(2)
            writer.empty()