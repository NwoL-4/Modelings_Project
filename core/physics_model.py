import numpy as np
from PySide6.QtWidgets import QLabel, QSpinBox, QLineEdit

import core.abstract_classes as abstract_classes
from utils import math_helpers, qt_helpers, methods, solvers


class NBody(abstract_classes.MainWidget):
    
    def __init__(self, name):
        super().__init__(name)

        self.colors_body = ['#%06X' % np.random.randint(0, 0xFFFFFF) for _ in range(100)]

        simSubheader = QLabel("Параметры симуляции")

        self.num_body_input = QSpinBox()
        self.num_body_input.setRange(2, 10)
        self.num_body_input.setValue(3)

        self.time_step_input = QLineEdit("10")

        self.num_iter_input = QSpinBox()
        self.num_iter_input.setRange(1, int(1e5))
        self.num_iter_input.setValue(1000)
        self.num_iter_input.valueChanged.connect(self.changed_num_veiw)

        self.num_view_input = QSpinBox()
        self.num_view_input.setRange(2, self.num_iter_input.value())
        self.num_view_input.setValue(self.num_iter_input.value() // 2)

        tableSubheader = QLabel("Параметры тел")

        _data = math_helpers.create_dataframe_Nbody(self.num_body_input.value(), self.colors_body)
        self.tableNbody = abstract_classes.SmartTableView(abstract_classes.SmartPandasModel(_data))

        self.num_body_input.valueChanged.connect(self.changed_model)

        self.inputs_widgets.addWidget(simSubheader)
        self.add_parameter_row("Число тел:", self.num_body_input)
        self.add_parameter_row("Временной шаг:", self.time_step_input)
        self.add_parameter_row("Число итераций:", self.num_iter_input)
        self.add_parameter_row("Число фреймов для вывода:", self.num_view_input)

        self.inputs_widgets.addWidget(tableSubheader)
        self.inputs_widgets.addWidget(self.tableNbody)

    def changed_num_veiw(self):
        self.num_view_input.setValue(self.num_iter_input.value())

    def changed_model(self):
        self.tableNbody.model = qt_helpers.update_row_count(self.num_body_input.value(), self.colors_body, self.tableNbody.model)

    def run_model(self):
        _data = self.tableNbody.model._data
        coord_x = np.array(_data['Координата x, м'].to_numpy(), dtype=float)
        coord_y = np.array(_data['Координата y, м'].to_numpy(), dtype=float)
        coord_z = np.array(_data['Координата z, м'].to_numpy(), dtype=float)

        speed_x = np.array(_data['Начальная скорость x, м/c'].to_numpy(), dtype=float)
        speed_y = np.array(_data['Начальная скорость y, м/c'].to_numpy(), dtype=float)
        speed_z = np.array(_data['Начальная скорость z, м/c'].to_numpy(), dtype=float)

        mass_body = np.array(_data['Масса, кг'].to_numpy(), dtype=float)
        radius_body = np.array(_data['Радиус, м'].to_numpy(), dtype=float)

        num_iter = self.num_iter_input.value()
        num_body = self.num_body_input.value()
        time_step = float(self.time_step_input.text())

        data = np.zeros((num_iter + 1, 2, 3, num_body))
        data[:] = np.nan

        data[0] = np.array([
            [coord_x, coord_y, coord_z],
            [speed_x, speed_y, speed_z]
        ])

        self.webEngine.bridge.create_plot('solar-system', {
            'type':'scatter3d',
            'layout': {
                'showlegend': False
            }
        })

        frame_data = [{
            'x': data[0, 0, 0].tolist(),
            'y': data[0, 0, 1].tolist(),
            'z': data[0, 0, 2].tolist(),
            'mode': 'lines+markers',
            'marker': {'size': 8, 'color': self.colors_body[:num_body]}
        }]

        self.webEngine.bridge.add_frame('solar-system', frame_data)

        ct = 0
        for i in range(1, num_iter + 1):
            collisions = math_helpers.collision_check(num_body=num_body,
                                               body_radius=radius_body,
                                               coordinate=data[i - 1, 0, :, :])
            if collisions:
                text = 'Моделирование завершено досрочно.'
                for collision in collisions:
                    text += f'\nСтолкнулись {collision[0]} и {collision[1]} тела'

                break
            ct += time_step

            data[i] = methods.rk4(ct, time_step, data[i - 1],
                                  solve=solvers.n_body_solve,
                                  func=mass_body)
        self.logger.add_log('Success')