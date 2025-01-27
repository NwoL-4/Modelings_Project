import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QComboBox,
    QPushButton, QLabel
)

import models


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выбор физической модели")
        self.setGeometry(150, 150, 400, 300)

        self.dict_models = {
            'N тел': models.Nbody,
            'Тепловое уравнение': models.HeatEq,
            'Колебания маятника': models.OscillPend
        }

        layout = QVBoxLayout()

        # Создание ComboBox для выбора модели
        self.model_selector = QComboBox()
        self.model_selector.addItems(list(self.dict_models.keys()))

        self.load_button = QPushButton("Загрузить модель")
        self.load_button.clicked.connect(self.load_model)

        layout.addWidget(QLabel("Выберите физическую модель:"))
        layout.addWidget(self.model_selector)
        layout.addWidget(self.load_button)

        self.setLayout(layout)

        self.model_windows = []

    def load_model(self):
        model_name = self.model_selector.currentText()
        selected_model = self.dict_models[model_name]()
        selected_model.show()
        self.model_windows.append(selected_model)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    # main_window = models.Nbody()
    main_window.show()
    sys.exit(app.exec())
