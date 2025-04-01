import numpy as np
import plotly.graph_objects as go
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from plotly.subplots import make_subplots

import core.abstract_classes as abstract_classes
from utils import math_helpers, qt_helpers, methods, solvers, plot_generators


class NBody(abstract_classes.MainWidget):

    def __init__(self, name):
        super().__init__(name)

        self.colors_body = ['#%06X' % np.random.randint(0, 0xFFFFFF) for _ in range(100)]
        simSubheader = QLabel("Параметры симуляции")
        simSubheader.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.num_body_input = abstract_classes.HelpSpinBox(help_text='Выберите число моделируемых тел от 2 до 10')
        self.num_body_input.setRange(2, 10)
        self.num_body_input.setValue(3)

        self.time_step_input = abstract_classes.HelpLineEdit(help_text='Выберите шаг моделирования')
        self.time_step_input.setText(str(0.05))

        self.num_iter_input = abstract_classes.HelpSpinBox(help_text='Выберите число фреймов для моделирования\n'
                                                                     '(Минимум:  10\n'
                                                                     ' Максимум: 1e7)')
        self.num_iter_input.setRange(10, int(1e7))
        self.num_iter_input.setValue(1000)
        self.num_iter_input.valueChanged.connect(self.change_view)

        self.num_view_input = abstract_classes.HelpSpinBox(
            help_text=f'Выберите число фреймов для отображения\n'
                      f'(Максимум: min(число фреймов для моделирования, 500)\n'
                      f' Минимум:  2)')
        self.num_view_input.setRange(2, 500)
        self.num_view_input.setValue(200)
        self.change_view()

        tableSubheader = QLabel("Параметры тел")

        _data = math_helpers.create_dataframe_Nbody(self.num_body_input.value(), self.colors_body)
        self.tableNbody = abstract_classes.TableViewer(_data)
        empty_label = QLabel("")
        empty_label.setFixedWidth(0)
        empty_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.num_body_input.valueChanged.connect(self.changed_model)

        self.inputs_widgets.addWidget(simSubheader)
        self.add_parameter_row("Число тел:", self.num_body_input)
        self.add_parameter_row("Временной шаг, с:", self.time_step_input)
        self.add_parameter_row("Число итераций:", self.num_iter_input)
        self.add_parameter_row("Число фреймов для вывода:", self.num_view_input)

        self.inputs_widgets.addWidget(tableSubheader)
        self.inputs_widgets.addWidget(self.tableNbody)

    def change_view(self):
        self.num_view_input.setRange(2, min(self.num_iter_input.value(), 500))

    def changed_model(self):
        self.tableNbody.model = qt_helpers.update_row_count(self.num_body_input.value(), self.colors_body,
                                                            self.tableNbody.model)
        self.tableNbody.update_table_size()

    def run_model(self):
        self.progressBar.setFormat("Моделирование завершено на: 0.00%")

        _data = self.tableNbody.model.df
        coord_x = np.array(_data['Координата x, м'].to_numpy(), dtype=float)
        coord_y = np.array(_data['Координата y, м'].to_numpy(), dtype=float)
        coord_z = np.array(_data['Координата z, м'].to_numpy(), dtype=float)

        speed_x = np.array(_data['Начальная скорость x, м/c'].to_numpy(), dtype=float)
        speed_y = np.array(_data['Начальная скорость y, м/c'].to_numpy(), dtype=float)
        speed_z = np.array(_data['Начальная скорость z, м/c'].to_numpy(), dtype=float)

        mass_body = np.array(_data['Масса, кг'].to_numpy(), dtype=float)
        radius_body = np.array(_data['Радиус, м'].to_numpy(), dtype=float)

        num_iter = self.num_iter_input.value()
        num_view = self.num_view_input.value()
        num_body = self.num_body_input.value()
        time_step = float(self.time_step_input.text().replace(',', '.'))

        frames_array = np.arange(num_iter + 1)[::num_iter // (num_view - 1)]

        data = np.zeros((num_iter + 1, 2, 3, num_body))
        data[:] = np.nan

        data[0] = np.array([
            [coord_x, coord_y, coord_z],
            [speed_x, speed_y, speed_z]
        ])

        self.init_fig(data[0, 0])

        self.create_frame(data, 0)

        ct = 0
        for i in range(1, num_iter + 1):
            collisions = math_helpers.collision_check(num_body=num_body,
                                                      body_radius=radius_body,
                                                      coordinate=data[i - 1, 0, :, :])
            if collisions:
                text = 'Моделирование завершено досрочно.'
                for collision in collisions:
                    text += f'\nСтолкнулись {collision[0]} и {collision[1]} тела'
                self.logger.log(text, abstract_classes.LogLevel.WARNING)
                self.progressBar.setValue(1000)
                break
            ct += time_step

            data[i] = methods.rk4(ct, time_step, data[i - 1],
                                  solve=solvers.n_body_solve,
                                  func=mass_body)
            if i in frames_array:
                self.create_frame(data, i)

            self.progressBar.setFormat(f"Моделирование завершено на: {i/num_iter * 100:.2f}%")
            self.progressBar.setValue(int(i / num_iter * 1000))

    def init_fig(self, data):
        # Создаем subplot
        fig = make_subplots(
            rows=1, cols=1,
            specs=[[{'type': 'scene'}, ], ],
            # subplot_titles=('', )
        )
        fig.update_layout(plot_generators.create_general_layout(),
                               # Настройки отображения маркеров
                               scattermode='overlay',
                               scattergap=0,
                               )
        fig.frames = []

        markers = plot_generators.generate_markers_nbody(data, self.colors_body)

        for i in range(len(markers)):
            fig.add_trace(
                markers[i],1, 1
            )

        tempdata = np.concatenate(([data], [data]), axis=0)
        lines = plot_generators.generate_lines_nbody(tempdata, self.colors_body)

        for i in range(len(lines)):
            fig.add_trace(lines[i], 1, 1)

        # Инициализируем график
        self.webEngine.bridge.init_plot(fig, self.webEngine.webView)


    def create_frame(self, data, index):
        slider = dict(
            label=str(index),
            method="animate",
            args=[[str(index)]]
        )
        markers = plot_generators.generate_markers_nbody(data[index, 0], self.colors_body)

        if index == 0:
            tempdata = np.concatenate(([data[index, 0]], [data[index, 0]]), axis=0)
            lines = plot_generators.generate_lines_nbody(tempdata, self.colors_body)
        else:
            lines = plot_generators.generate_lines_nbody(data[:index + 1, 0], self.colors_body)

        figure_list = markers + lines

        frame = go.Frame(
            name=str(index),
            data=figure_list,
            traces=list(range(len(figure_list)))
        )

        self.webEngine.bridge.add_frame(frame, slider, self.webEngine.webView)


class HeatEq(abstract_classes.MainWidget):
    def __init__(self, name):
        super().__init__(name)

        simSubheader = QLabel("Параметры симуляции")
        plateSubheader = QLabel("Параметры пластины")
        boundSubheader = QLabel("Начальные и граничные условия")

        self.num_nodes_input = abstract_classes.HelpSpinBox(help_text="Выберите число узлов сетки\n"
                                                                      "(Минимум:  2,"
                                                                      " Максимум: 1000)")
        self.num_nodes_input.setRange(2, 1000)
        self.num_nodes_input.setValue(100)

        self.num_iter_input = abstract_classes.HelpSpinBox(help_text="Выберите время моделирования")
