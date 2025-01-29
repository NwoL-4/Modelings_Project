import os
from itertools import product

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QSpinBox, QLineEdit, QHBoxLayout, QPushButton, QTableView, QProgressBar,
    QRadioButton, QFrame, QCheckBox,
)

import scipy.constants as const
from pyarrow import duration

import utils

css = """
    QWidget {
        font-family: Bahnschrift;
        font-size: 12pt;
        background-color: #FFFFFF;  /* Фон окна */
        color: #31333F;  /* Цвет текста */
    }
    QSpinBox {
        height: 24px;
        border-radius: 5px;
        background-color: #F0F2F6;  /* Фон редактируемых полей */
        border: 1px solid #FF4B4B;  /* Окантовка полей */
    }
    QLineEdit {
        height: 22px;
        border-radius: 5px;
        background-color: #F0F2F6;  /* Фон редактируемых полей */
        border: 1px solid #FF4B4B;  /* Окантовка полей */
    }
    QPushButton {
        height: 20px;
        border-radius: 5px;
        border: 2px solid #FF4B4B;  /* Окантовка кнопок */
        background-color: #FFFFFF;  /* Фон кнопок */
        padding: 5px;
    }
    QPushButton:hover {
        color: #FF4B4B;
    }
"""


class Nbody(QWidget):
    def __init__(self):
        super().__init__()

        self.name = 'Модель N тел'
        self.setWindowTitle(self.name)
        self.setGeometry(150, 150, 1200, 800)

        self.init_variables()

        self.setStyleSheet(css)

        mainLayout = QVBoxLayout()

        self.columns_layout = QHBoxLayout()

        self.sim_column()
        self.table_column()

        mainLayout.addLayout(self.columns_layout)
        mainLayout.setAlignment(self.columns_layout, Qt.AlignmentFlag.AlignTop)
        self.setLayout(mainLayout)

        self.run_button = QPushButton("Запустить модель")
        self.run_button.hide()

        self.run_button.clicked.connect(self.run_model)

        self.webview = QWebEngineView(self)
        self.webview.setFixedHeight(int(self.window_height // 1.7))
        mainLayout.addWidget(self.webview)
        mainLayout.setAlignment(self.webview, Qt.AlignmentFlag.AlignTop)

        mainLayout.addWidget(self.run_button)
        mainLayout.addWidget(self.collision)
        mainLayout.addWidget(self.progress_bar)

    def init_variables(self):
        self.num_body = 0
        self.num_view = 0
        self.num_iter = 0
        self.time_step = 0
        self.colors_body = ['#%06X' % np.random.randint(0, 0xFFFFFF) for _ in range(20)]
        self.data_ = self.create_initial_dataframe()

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.collision = QLabel('')
        self.collision.hide()
        self.submit_table_button = None

        self.model = None

        self.coord_x = None
        self.coord_y = None
        self.coord_z = None
        self.speed_x = None
        self.speed_y = None
        self.speed_z = None
        self.mass_body = None
        self.radius_body = None

        self.window_width = self.width()
        self.window_height = self.height()

    def resizeEvent(self, event):
        # Получаем текущие размеры окна
        self.window_width = self.width()
        self.window_height = self.height()

        super().resizeEvent(event)

    def timer(self, text, Layout):
        text_view = QLabel(text)
        Layout.addWidget(text_view)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.remove_label(text_view))
        timer.start(2000)

    def remove_label(self, label):
        self.firstLayout.removeWidget(label)
        label.deleteLater()

    def sim_column(self):
        self.firstLayout = QFormLayout()

        self.simSubheader = QLabel('Параметры симуляции')

        self.num_body_input = QSpinBox()
        self.num_body_input.setRange(2, 10)
        self.num_body_input.setValue(3)

        self.time_step_input = QLineEdit("10")

        self.num_iter_input = QSpinBox()
        self.num_iter_input.setRange(1, int(1e5))
        self.num_iter_input.setValue(1000)

        self.num_view_input = QSpinBox()
        self.num_view_input.setRange(2, self.num_iter_input.value())
        self.num_view_input.setValue(self.num_iter_input.value() // 2)

        self.firstLayout.addRow(self.simSubheader)
        self.firstLayout.addRow("Число тел:", self.num_body_input)
        self.firstLayout.addRow("Временной шаг:", self.time_step_input)
        self.firstLayout.addRow("Число итераций:", self.num_iter_input)
        self.firstLayout.addRow("Число фреймов для вывода:", self.num_view_input)

        self.submit_sim_button = QPushButton("Отправить параметры симуляции")
        self.submit_sim_button.clicked.connect(self.submit_simulation_params)

        self.firstLayout.addWidget(self.submit_sim_button)
        self.columns_layout.addLayout(self.firstLayout)


    def submit_simulation_params(self):
        self.num_body = self.num_body_input.value()
        self.time_step = float(self.time_step_input.text())
        self.num_iter = self.num_iter_input.value()
        self.num_view = self.num_view_input.value()

        self.timer('Данные добавлены', self.firstLayout)
        self.update_row_count()

        self.tableSubheader.show()
        self.tableNbody.show()
        self.submit_table_button.show()

    def table_column(self):
        self.secondLayout = QFormLayout()

        self.tableSubheader = QLabel('Параметры тел')
        self.tableSubheader.hide()
        self.tableNbody = QTableView()
        self.model = utils.PandasModel(self.data_)
        self.tableNbody.setModel(self.model)
        self.tableNbody.setFixedHeight(114)

        self.tableNbody.hide()

        self.submit_table_button = QPushButton("Отправить параметры из таблицы")
        self.submit_table_button.hide()

        self.submit_table_button.clicked.connect(self.submit_table_params)

        self.secondLayout.addRow(self.tableSubheader)
        self.secondLayout.addRow(self.tableNbody)
        self.secondLayout.addRow(self.submit_table_button)

        self.secondLayout.setAlignment(self.tableNbody, Qt.AlignmentFlag.AlignTop)
        self.secondLayout.setAlignment(self.submit_table_button, Qt.AlignmentFlag.AlignTop)

        self.columns_layout.addLayout(self.secondLayout)

    def create_initial_dataframe(self):
        data = {
            'Номер тела': np.arange(self.num_body) + 1,
            'Цвет тела': self.colors_body[:self.num_body],
            'Масса, кг': ['0'] * self.num_body,
            'Радиус, м': ['0'] * self.num_body,
            'Начальная скорость x, м/c': ['0'] * self.num_body,
            'Начальная скорость y, м/c': ['0'] * self.num_body,
            'Начальная скорость z, м/c': ['0'] * self.num_body,
            'Координата x, м': ['0'] * self.num_body,
            'Координата y, м': ['0'] * self.num_body,
            'Координата z, м': ['0'] * self.num_body,
        }
        return pd.DataFrame(data)

    def update_row_count(self):
        new_row_count = self.num_body
        current_row_count = self.model.rowCount()

        new_data = pd.DataFrame(columns=self.model._data.columns)
        for i in range(min(current_row_count, new_row_count)):
            new_data.loc[i] = self.model._data.iloc[i]
        for i in range(current_row_count, new_row_count):
            new_data.loc[i] = ['0'] * len(self.model._data.columns)
            new_data.loc[i, 'Номер тела'] = i + 1
            new_data.loc[i, 'Цвет тела'] = self.colors_body[i]

        self.model._data = new_data
        self.model.layoutChanged.emit()

    def submit_table_params(self):
        new_data = self.model._data.copy()

        self.coord_x = np.array(new_data['Координата x, м'].to_numpy(), dtype=float)
        self.coord_y = np.array(new_data['Координата y, м'].to_numpy(), dtype=float)
        self.coord_z = np.array(new_data['Координата z, м'].to_numpy(), dtype=float)

        self.speed_x = np.array(new_data['Начальная скорость x, м/c'].to_numpy(), dtype=float)
        self.speed_y = np.array(new_data['Начальная скорость y, м/c'].to_numpy(), dtype=float)
        self.speed_z = np.array(new_data['Начальная скорость z, м/c'].to_numpy(), dtype=float)

        self.mass_body = np.array(new_data['Масса, кг'].to_numpy(), dtype=float)
        self.radius_body = np.array(new_data['Радиус, м'].to_numpy(), dtype=float)

        self.timer('Данные добавлены', self.secondLayout)

        self.run_button.show()

    def run_model(self):
        data = np.zeros((self.num_iter + 1, 2, 3, self.num_body))
        data[:] = np.nan

        data[0] = np.array([
            [self.coord_x, self.coord_y, self.coord_z],
            [self.speed_x, self.speed_y, self.speed_z]
        ])

        ct = 0

        self.progress_bar.show()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        self.collision.hide()

        for i in range(1, self.num_iter + 1):
            collisions = utils.collision_check(num_body=self.num_body,
                                               body_radius=self.radius_body,
                                               coordinate=data[i - 1, 0, :, :])
            if collisions != []:
                text = 'Моделирование завершено досрочно.'
                for collision in collisions:
                    text += f'\nСтолкнулись {collision[0]} и {collision[1]} тела'
                self.collision.show()
                self.collision.setText(text)
                break
            ct += self.time_step

            data[i] = utils.rk4(ct, self.time_step, data[i - 1],
                                solve=utils.n_body_solve,
                                func=self.mass_body)
            self.progress_bar.setValue(int(i / self.num_iter * 100))
            self.progress_bar.setFormat(f"Моделирование выполнено на {i / self.num_iter * 100:.2f}%")
        self.show_plot(data[:, 0, :, :])


    def show_plot(self, coordinate):
        fig = go.Figure()

        size = 20
        width = 5

        duration = 15

        self.progress_bar.setValue(0)

        step = coordinate.shape[0] // self.num_view

        indexes_range = range(0, coordinate.shape[0], step)
        body_range = range(coordinate.shape[2])

        for body in body_range:
            fig.add_trace(go.Scatter3d(
                x=[coordinate[0, 0, body]],
                y=[coordinate[0, 1, body]],
                z=[coordinate[0, 2, body]],
                mode='markers',
                marker=dict(
                    color=self.colors_body[body],
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
                    color=self.colors_body[body],
                    width=width
                ),
                name=f'Траектория {body + 1} тела'
            ))

        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f'Визуализация завершена на {0}')

        frames = []

        for index in indexes_range:

            data = []

            for body in body_range:
                data.append(go.Scatter3d(
                    x=[coordinate[index, 0, body]],
                    y=[coordinate[index, 1, body]],
                    z=[coordinate[index, 2, body]],
                    mode='markers',
                    marker=dict(
                        color=self.colors_body[body],
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
                        color=self.colors_body[body],
                        width=width
                    ),
                    name=f'Траектория {body + 1} тела'
                ))

            frames.append(go.Frame(name=str(index),
                                   data=data
                                   ))
            self.progress_bar.setValue(int((index + 1) / coordinate.shape[0] * 100))
            self.progress_bar.setFormat(f'Визуализация завершена на {(index + 1) / coordinate.shape[0] * 100:.2f}%')

        steps = []
        for index in indexes_range:
            step = dict(
                label=str(index),
                method='animate',
                args=[[str(index)], dict(frame={"duration": duration, "redraw": True}, mode="immediate")]
            )
            steps.append(step)

        sliders = [dict(
            steps=steps,
        )]

        fig.update_layout(
            # plot_bgcolor=theme['backgroundColor'],
            # paper_bgcolor=theme['backgroundColor'],
            # font=dict(
            #     family=theme['font'],
            #     color=theme['textColor'],
            # ),
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
            updatemenus=[dict(
                direction="left",
                pad=dict(r=10, t=87),
                xanchor="center",
                yanchor="top",
                x=1.05,
                y=0.5,
                showactive=False,
                type="buttons",
                buttons=[
                    dict(label="►", method="animate", args=[None,
                                                            {"frame": {"duration": duration, "redraw": True},
                                                             "mode": "immediate",
                                                             "transition": {"duration": 0}},
                                                            # {"fromcurrent": True}
                                                            ]),
                    dict(label="❚❚", method="animate",
                         args=[[None], {"frame": {"duration": duration, "redraw": True},
                                        "mode": "immediate",
                                        "transition": {"duration": 0}}])])],
        )
        fig.layout.sliders = sliders
        fig.frames = frames

        plot_html = os.path.join(os.getcwd(), 'plot_nBody.html')
        fig.write_html(plot_html)

        self.webview.setUrl(QUrl.fromLocalFile(plot_html))
        self.webview.show()
        self.progress_bar.hide()

class HeatEq(QWidget):
    def __init__(self):
        super().__init__()

        self.name = 'Тепловое уравнение'
        self.setWindowTitle(self.name)
        self.setGeometry(150, 150, 1200, 800)

        self.init_variables()

        self.setStyleSheet(css)

        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        self.columns_layout = QHBoxLayout()
        mainLayout.addLayout(self.columns_layout)

        self.first_layout = QVBoxLayout()
        self.columns_layout.addLayout(self.first_layout)

        self.params_layout = QFormLayout()
        self.first_layout.addLayout(self.params_layout, 1)
        self.bound_layout = QFormLayout()
        self.first_layout.addLayout(self.bound_layout, 1)

        self.view_layout = QFormLayout()
        self.columns_layout.addLayout(self.view_layout, 1)

        self.params_column()

        self.sumbit_params_button = QPushButton('Отправить все параметры')
        self.sumbit_params_button.clicked.connect(self.submit_params)
        self.first_layout.addWidget(self.sumbit_params_button)

        self.run_button = QPushButton("Запустить модель")
        self.run_button.hide()

        self.run_button.clicked.connect(self.run_model)

        self.timeText = QLabel('')
        self.timeText.hide()
        self.view_layout.addRow(self.timeText)
        self.view_layout.addRow(self.progress_bar)

        self.webview = QWebEngineView(self)
        self.webview.setUrl('plot_n_body.html')
        self.webview.setFixedHeight(int(self.window_height // 1.7))
        self.view_layout.addWidget(self.webview)

        mainLayout.addWidget(self.run_button)

    def init_variables(self):
        self.window_width = self.width()
        self.window_height = self.height()
        self.num_view = None
        self.num_iter = None
        self.time_step = None
        self.num_nodes = None

        self.boundary_type = None

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.hide()
        self.temperature = None

    def resizeEvent(self, event):
        # Получаем текущие размеры окна
        self.window_width = self.width()
        self.window_height = self.height()

        super().resizeEvent(event)

    def timer(self, text, Layout):
        text_view = QLabel(text)
        Layout.addWidget(text_view)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.remove_label(text_view, Layout))
        timer.start(2000)

    def remove_label(self, label, Layout):
        Layout.removeWidget(label)
        label.deleteLater()

    def add_line(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setLineWidth(5)
        line.setFixedHeight(5)
        layout.addRow(line)

    def params_column(self):
        self.simSubheader = QLabel('Параметры симуляции')
        self.plateSubheader = QLabel("Параметры пластины")
        self.boundSubheader = QLabel('Начальные и граничные условия')

        self.num_nodes_input = QSpinBox()
        self.num_iter_input = QSpinBox()
        self.num_view_input = QSpinBox()

        self.num_nodes_input.setRange(2, 1000)
        self.num_nodes_input.setValue(100)
        self.num_iter_input.setRange(1, int(1e5))
        self.num_iter_input.setValue(1000)
        self.num_view_input.setRange(2, self.num_iter_input.value())
        self.num_view_input.setValue(self.num_iter_input.value() // 2)
        self.use_source = QCheckBox("Включить источник")
        self.use_source.setChecked(True)

        self.size_x_input = QLineEdit("0.1")
        self.size_y_input = QLineEdit("0.1")
        self.coef_thermal_input = QLineEdit("1.11e-4")
        self.power_source_input = QLineEdit("1")
        self.radius_source_input = QLineEdit("1e-2")
        self.xSource_percent = QLineEdit("50")
        self.ySource_percent = QLineEdit("50")

        self.use_source.stateChanged.connect(self.update_source)

        self.init_temp_input = QLineEdit("300")
        self.options = ['Температура одинакова на всех границах',
                        'Различная температура на границах',
                        'Различные температуры на углах']
        self.radio1 = QRadioButton(self.options[0])
        self.radio2 = QRadioButton(self.options[1])
        self.radio3 = QRadioButton(self.options[2])

        self.radio1.toggled.connect(self.update_form)
        self.radio2.toggled.connect(self.update_form)
        self.radio3.toggled.connect(self.update_form)

        self.params_layout.addRow(self.simSubheader)
        self.params_layout.addRow("Число узлов вдоль каждой оси:", self.num_nodes_input)
        self.params_layout.addRow("Число итераций:", self.num_iter_input)
        self.params_layout.addRow("Число фреймов для отображения:", self.num_view_input)
        self.params_layout.addWidget(self.use_source)
        self.add_line(self.params_layout)

        self.params_layout.addRow(self.plateSubheader)
        self.params_layout.addRow("Размер пластины вдоль x, м", self.size_x_input)
        self.params_layout.addRow("Размер пластины вдоль y, м", self.size_y_input)
        self.params_layout.addRow("Коэффициент теплопроводности, м^2/c", self.coef_thermal_input)
        self.params_layout.addRow("Мощность источника, Вт", self.power_source_input)
        self.params_layout.addRow("Радиус источника, м", self.radius_source_input)
        self.params_layout.addRow("Расположение источника по оси x, %"
                                  "\n(в процентах от размера пластины вроль x)", self.xSource_percent)
        self.params_layout.addRow("Расположение источника по оси y, %"
                                  "\n(в процентах от размера пластины вроль y)", self.ySource_percent)

        self.add_line(self.params_layout)

        self.params_layout.addRow(self.boundSubheader)
        self.params_layout.addRow("Начальная температура, К", self.init_temp_input)
        self.params_layout.addWidget(self.radio1)
        self.params_layout.addWidget(self.radio2)
        self.params_layout.addWidget(self.radio3)

    def update_source(self):
        if self.use_source.isChecked():
            self.power_source_input.show()
            self.radius_source_input.show()
            self.xSource_percent.show()
            self.ySource_percent.show()
        else:
            self.power_source_input.hide()
            self.radius_source_input.hide()
            self.xSource_percent.hide()
            self.ySource_percent.hide()

    def update_form(self, choice):
        while self.bound_layout.rowCount() > 0:
            self.bound_layout.removeRow(0)
        if self.radio1.isChecked():
            self.boundary_type = self.options[0]
            self.all_bound_input = QLineEdit("273")
            self.bound_layout.addRow("Температура границы, К", self.all_bound_input)
        elif self.radio2.isChecked():
            self.boundary_type = self.options[1]
            self.upBound_input = QLineEdit("273")
            self.downBound_input = QLineEdit("273")
            self.leftBound_input = QLineEdit("273")
            self.rightBound_input = QLineEdit("273")

            self.bound_layout.addRow("Температура верхней границы, К", self.upBound_input)
            self.bound_layout.addRow("Температура нижней границы, К", self.downBound_input)
            self.bound_layout.addRow("Температура левой границы, К", self.leftBound_input)
            self.bound_layout.addRow("Температура правой границы, К", self.rightBound_input)
        elif self.radio3.isChecked():
            self.boundary_type = self.options[2]
            self.ulBound_input = QLineEdit("273")
            self.dlBound_input = QLineEdit("273")
            self.urBound_input = QLineEdit("273")
            self.drBound_input = QLineEdit("273")

            self.bound_layout.addRow("Температура верхнего левого угла, К", self.ulBound_input)
            self.bound_layout.addRow("Температура нижнего левого угла, К", self.dlBound_input)
            self.bound_layout.addRow("Температура верхнего правого угла, К", self.urBound_input)
            self.bound_layout.addRow("Температура нижнего правого угла, К", self.drBound_input)

    def submit_params(self):
        self.num_nodes = self.num_nodes_input.value()
        self.num_iter = self.num_iter_input.value()
        self.num_view = self.num_view_input.value()

        self.size_x = float(self.size_x_input.text())
        self.size_y = float(self.size_y_input.text())

        self.boolSource = self.use_source.isChecked()
        self.coef_thermal = float(self.coef_thermal_input.text())
        self.power_source = float(self.power_source_input.text())
        self.radius_source = float(self.radius_source_input.text())
        self.xSource = float(self.xSource_percent.text()) / 100 * self.size_x
        self.ySource = float(self.ySource_percent.text()) / 100 * self.size_y

        self.tempSource = (self.power_source /
                           (const.Stefan_Boltzmann * np.pi * (self.radius_source ** 2))
        ) ** (1 / 4)

        self.x_range = np.linspace(0, self.size_x, num=self.num_nodes, endpoint=True)
        self.y_range = np.linspace(0, self.size_y, num=self.num_nodes, endpoint=True)

        self.hx = np.mean(np.diff(self.x_range))
        self.hy = np.mean(np.diff(self.y_range))

        self.time_step = 1 / 2 * self.hx * self.hy

        self.time_array = np.arange(self.num_iter) * self.time_step

        self.timeText.setText(f'Будет промоделировано {self.time_array[-1]} с')
        self.timeText.show()

        self.init_temp = float(self.init_temp_input.text())

        self.temperature = np.zeros((self.num_iter + 1, self.num_nodes, self.num_nodes),
                                     dtype=float)

        self.temperature[0] = self.init_temp

        match self.boundary_type:
            case 'Температура одинакова на всех границах':
                all_bound = float(self.all_bound_input.text())
                self.temperature[0, 0, :] =\
                self.temperature[0, -1, :] =\
                self.temperature[0, :, 0] =\
                self.temperature[0, :, -1] = all_bound
            case 'Различная температура на границах':
                leftBound = float(self.leftBound_input.text())
                rightBound = float(self.rightBound_input.text())
                downBound = float(self.downBound_input.text())
                upBound = float(self.upBound_input.text())
                self.temperature[0, :, 0] = leftBound
                self.temperature[0, :, -1] = rightBound
                self.temperature[0, 0, :] = downBound
                self.temperature[0, -1, :] = upBound
                self.temperature[0, 0, 0] = np.mean([leftBound, downBound])
                self.temperature[0, -1, 0] = np.mean([leftBound, upBound])
                self.temperature[0, 0, -1] = np.mean([rightBound, downBound])
                self.temperature[0, -1, -1] = np.mean([rightBound, upBound])
            case 'Различные температуры на углах':
                drBound = float(self.drBound_input.text())
                dlBound = float(self.dlBound_input.text())
                urBound = float(self.urBound_input.text())
                ulBound = float(self.ulBound_input.text())

                self.temperature[0, 0, :] = self.x_range * (
                    drBound - dlBound) / self.size_x + dlBound
                self.temperature[0, :, 0] = self.y_range * (
                    ulBound - dlBound) / self.size_y + dlBound
                self.temperature[0, -1, :] = self.x_range * (
                    urBound - ulBound) / self.size_x + ulBound
                self.temperature[0, :, -1] = self.y_range * (
                    urBound - drBound) / self.size_y + drBound
        if self.boolSource:
            self.temperature[0] = self.get_temp_source(self.temperature[0])

        self.run_button.show()

    def get_temp_source(self, temp):
        new_temp = temp.copy()


        for x, y in product(range(self.x_range.shape[0]), range(self.y_range.shape[0])):
            if ((self.x_range[x] - self.xSource) ** 2 +
                (self.y_range[y] - self.ySource) ** 2 <= self.radius_source ** 2):
                new_temp[x, y] = self.tempSource

        return new_temp


    def run_model(self):
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"Моделирование выполнено на {0:.2f}%")
        for index_t in range(1, self.num_iter + 1):
            self.temperature[index_t] = utils.euler_Method(
                temperature=self.temperature[index_t - 1],
                time_step=self.time_step,
                alpha=self.coef_thermal,
                hx=self.hx,
                hy=self.hy
            )
            if self.boolSource:
                self.temperature[index_t] = self.get_temp_source(self.temperature[index_t])

            self.progress_bar.setValue(int(index_t / self.num_iter))
            self.progress_bar.setFormat(f"Моделирование выполнено на {index_t / self.num_iter * 100:.2f}%")
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat('Моделирование завершено')

        self.show_plot()

    def show_plot(self):
        fig = go.Figure()

        duration = 15

        self.progress_bar.setValue(0)

        step = self.temperature.shape[0] // self.num_view

        indexes_range = range(0, self.temperature.shape[0], step)

        color_slice = 20

        minTemp = np.min(self.temperature)
        maxTemp = np.max(self.temperature)

        fig.add_trace(
            go.Contour(
                x=self.x_range,
                y=self.y_range,
                z=self.temperature[0],
                colorscale='inferno',
                colorbar=dict(
                    thicknessmode='pixels',
                    len=1.3,
                    lenmode='fraction',
                    outlinewidth=1
                ),
                contours=dict(
                    coloring='heatmap',
                    start=minTemp,
                    end=maxTemp,
                    size=(maxTemp - minTemp) / color_slice,
                ),
            )
        )

        frames = []
        for index in indexes_range:
            frames.append(go.Frame(name=str(index), data=[
                go.Contour(
                    x=self.x_range,
                    y=self.y_range,
                    z= self.temperature[index],
                    colorscale='inferno',
                    colorbar=dict(
                        thicknessmode='pixels',
                        len=1.3,
                        lenmode='fraction',
                        outlinewidth=1
                    ),
                    contours=dict(
                        coloring='heatmap',
                        start=minTemp,
                        end=maxTemp,
                        size=(maxTemp - minTemp) / color_slice,
                    ),
                )
            ]))
            self.progress_bar.setValue(int((index + 1) / self.temperature.shape[0] * 100))
            self.progress_bar.setFormat(f'Визуализация завершена на {(index + 1) / self.temperature.shape[0] * 100:.2f}%')


        steps = []
        for index in indexes_range:
            step = dict(
                label=str(index),
                method='animate',
                args=[[str(index)], dict(frame={"duration": duration, "redraw": True}, mode="immediate")]
            )
            steps.append(step)

        sliders = [dict(
            steps=steps,
        )]

        fig.update_layout(
            xaxis=dict(
                range=[self.x_range[0], self.x_range[-1]]
            ),
            yaxis=dict(
                range=[self.y_range[0], self.y_range[-1]]
            ),
            height=700,
            updatemenus=[dict(
                direction="left",
                pad=dict(r=10, t=87),
                xanchor="center",
                yanchor="top",
                x=1.05,
                y=0.5,
                showactive=False,
                type="buttons",
                buttons=[
                    dict(label="►", method="animate", args=[None,
                                                            {"frame": {"duration": duration, "redraw": True},
                                                             "mode": "immediate",
                                                             "transition": {"duration": 0}},
                                                            # {"fromcurrent": True}
                                                            ]),
                    dict(label="❚❚", method="animate",
                         args=[[None], {"frame": {"duration": duration, "redraw": True},
                                        "mode": "immediate",
                                        "transition": {"duration": 0}}])])],
        )
        fig.layout.sliders = sliders
        fig.frames = frames

        plot_html = os.path.join(os.getcwd(), 'plot_heatEq.html')
        fig.write_html(plot_html)

        self.webview.setUrl(QUrl.fromLocalFile(plot_html))
        self.webview.setFixedHeight(800)
        self.webview.show()
        self.progress_bar.hide()


class OscillPend(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Колебания маятника'
        self.setWindowTitle(self.name)
        self.setGeometry(150, 150, 1200, 800)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Настройки теплового уравнения (в разработке)"))
        self.setLayout(layout)

