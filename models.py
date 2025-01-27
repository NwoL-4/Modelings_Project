import os

import numpy as np
import pandas as pd
from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QResizeEvent
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QSpinBox, QLineEdit, QHBoxLayout, QPushButton, QTableView, QProgressBar,
)

import plotly.graph_objects as go

import utils


class Nbody(QWidget):
    def __init__(self):
        super().__init__()

        self.name = 'Модель N тел'
        self.setWindowTitle(self.name)
        self.setGeometry(150, 150, 1200, 800)

        self.init_variables()

        self.setStyleSheet("""
                    QWidget {
                        background-color: #FFFFFF;  /* Фон окна */
                        color: #31333F;  /* Цвет текста */
                    }
                    QLineEdit, QSpinBox {
                        border-radius: 5px;
                        background-color: #F0F2F6;  /* Фон редактируемых полей */
                        border: 1px solid #FF4B4B;  /* Окантовка полей */
                    }
                    QPushButton {
                        border-radius: 5px;
                        border: 2px solid #FF4B4B;  /* Окантовка кнопок */
                        background-color: #FFFFFF;  /* Фон кнопок */
                        padding: 5px;
                    }
                    QPushButton:hover {
                        color: #FF4B4B;
                    }
                """)

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
        # self.webview.setMinimumHeight(self.window_height // 1.5)
        self.webview.setFixedHeight(self.window_height // 1.7)
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

    def sim_column(self):
        self.firstLayout = QFormLayout()

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

        self.firstLayout.addRow("Число тел:", self.num_body_input)
        self.firstLayout.addRow("Временной шаг:", self.time_step_input)
        self.firstLayout.addRow("Число итераций", self.num_iter_input)
        self.firstLayout.addRow("Число фреймов для вывода", self.num_view_input)

        self.submit_sim_button = QPushButton("Отправить параметры симуляции")
        self.submit_sim_button.clicked.connect(self.submit_simulation_params)

        self.firstLayout.addWidget(self.submit_sim_button)

        self.columns_layout.addLayout(self.firstLayout)

    def table_column(self):
        self.secondLayout = QFormLayout()

        self.tableNbody = QTableView()
        self.model = utils.PandasModel(self.data_)
        self.tableNbody.setModel(self.model)
        self.tableNbody.setFixedHeight(102 * 2)

        self.tableNbody.hide()

        self.submit_table_button = QPushButton("Отправить параметры из таблицы")
        self.submit_table_button.hide()

        self.submit_table_button.clicked.connect(self.submit_table_params)

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

    def submit_simulation_params(self):
        self.num_body = self.num_body_input.value()
        self.time_step = float(self.time_step_input.text())
        self.num_iter = self.num_iter_input.value()
        self.num_view = self.num_view_input.value()

        self.timer('Данные добавлены', self.firstLayout)
        self.update_row_count()

        self.tableNbody.show()
        self.submit_table_button.show()

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
                args=[[str(index)]]
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
                    dict(label="►", method="animate", args=[None, {"fromcurrent": True}]),
                    dict(label="❚❚", method="animate",
                         args=[[None], {"frame": {"duration": 50, "redraw": False},
                                        "mode": "immediate",
                                        "transition": {"duration": 0}}])])],
        )
        fig.layout.sliders = sliders
        fig.frames = frames

        plot_html = os.path.join(os.getcwd(), 'plot.html')
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

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Настройки теплового уравнения (в разработке)"))
        self.setLayout(layout)

class OscillPend(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Колебания маятника'
        self.setWindowTitle(self.name)
        self.setGeometry(150, 150, 1200, 800)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Настройки теплового уравнения (в разработке)"))
        self.setLayout(layout)
