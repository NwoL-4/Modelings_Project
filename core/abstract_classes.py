from datetime import datetime

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QUrl, QSize, Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget, QTextEdit, QScrollArea, QLabel, QHBoxLayout, QPushButton, \
    QFormLayout, QSizePolicy, QTableView, QComboBox

import utils.file_operations
import utils.file_operations as file_operations
import utils.js_helpers as js_helpers
import utils.qt_helpers as qt_helpers




class Logger(QWidget):
    def __init__(self):
        super().__init__()

        self.logger = QComboBox()
        self.logger.setMinimumHeight(30)

        logger_layout = QVBoxLayout(self)

        logger_layout.addWidget(self.logger)

    def add_log(self, text):
        timer = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.logger.addItem(f'[{timer}]---{text}')


class ExpandableLog(QWidget):
    def __init__(self):
        super().__init__()
        self._collapsed_height = 100
        self._expanded_height = 100

        self.layout = QVBoxLayout(self)
        self.log_area = QTextEdit()
        # self.log_area.setEnabled(False)

        self.scroll = QScrollArea()
        self.scroll.setWidget(self.log_area)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(100)

        self.animation = QPropertyAnimation(self.log_area, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.layout.addWidget(self.scroll)

        self.log_area.setMaximumHeight(self._collapsed_height)

    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")
        full_message = f"[{timestamp}] {message}"
        self.log_area.append(full_message)


class webViewWrapper(QWidget):
    def __init__(self, path_to_html):
        super().__init__()

        self.path_to_html = path_to_html

        layout = QVBoxLayout()

        self.webView = QWebEngineView()
        self.channel = QWebChannel()
        self.bridge = js_helpers.PythonJsBridge()

        self.channel.registerObject("bridge", self.bridge)
        self.webView.page().setWebChannel(self.channel)

        self.load_initial_html()

        layout.addWidget(self.webView)

        self.setLayout(layout)

    def load_initial_html(self):

        with open(self.path_to_html, mode='w') as f:
            f.write(js_helpers.generate_html_code())

        self.webView.load(QUrl.fromLocalFile(self.path_to_html))

    def update_plot(self, data, rows=1, cols=1):
        """Пример вызова из python для обновленипя графика"""
        self.bridge.add_frame(
            data=[
                {
                    'x': frame_data[0].tolist(),
                    'y': frame_data[1].tolist()
                } for frame_data in data
            ],
            cols=cols,
            rows=rows
        )


class SmartPandasModel(QAbstractTableModel):
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
            if role == Qt.ItemDataRole.BackgroundRole:
                if index.column() == 1:
                    color = self._data.iloc[index.row(), index.column()]
                    return QColor(color)
        return None

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


class SmartTableView(QWidget):

    def __init__(self, model):
        super().__init__()

        table = TableView()

        self.model = model

        table.setModel(self.model)

        table_layout = QVBoxLayout(self)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(table)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        header = table.horizontalHeader()
        header.setStretchLastSection(True)


class TableView(QTableView):
    def __init__(self):
        super().__init__()

    def resizeEvent(self, event):
        height = self.horizontalHeader().height()
        for row in range(self.model().rowCount()):
            height += self.rowHeight(row)

        if self.horizontalScrollBar().isVisible():
            height += self.horizontalScrollBar().height()
        self.setFixedHeight(height + 2)


class MainWidget(QWidget):

    def __init__(self, name):
        super().__init__()
        self.setWindowTitle(name)
        self.setGeometry(150, 150, 1200, 800)
        self.setMinimumSize(QSize(1200, 800))
        self.setStyleSheet(qt_helpers.css)

        self.temppath = utils.file_operations.create_file(self.__class__.__name__)

        # Основной layout
        layout = QVBoxLayout()

        # Элементы основного layout
        title = QLabel(f'Добро пожаловать в {name}')
        main_layout = QHBoxLayout()

        layout.addWidget(title)
        layout.addLayout(main_layout)

        # Элементы main_layout
        inputs_container = QWidget()
        inputs_layout = QVBoxLayout(inputs_container)
        self.webEngine = webViewWrapper(path_to_html=self.temppath[1])

        scroll_area = QScrollArea()

        # Настойка растягивания компонентов
        inputs_layout.addWidget(scroll_area, 1) # 100% доступного пространства

        # Контейнер для нижнего блока
        bottom_block = QWidget()
        bottom_layout = QVBoxLayout(bottom_block)
        bottom_layout.setContentsMargins(0, 10, 0, 0) # Отступ сверху

        inputs_layout.addWidget(bottom_block, 0) # Фиксированная высота

        self.runner = QPushButton('Запуск модели')
        self.runner.clicked.connect(self.run_model)

        self.logger = Logger()

        bottom_layout.addWidget(self.runner, alignment=Qt.AlignmentFlag.AlignHCenter)
        bottom_layout.addWidget(self.logger)

        # Костыль на scroll_area
        widget = QWidget()
        self.inputs_widgets = QFormLayout()
        self.inputs_widgets.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.inputs_widgets.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.inputs_widgets.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        self.inputs_widgets.setVerticalSpacing(10)
        self.inputs_widgets.setHorizontalSpacing(15)

        widget.setLayout(self.inputs_widgets)
        scroll_area.setWidget(widget)

        # Настройка всех элементов
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(350)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Обновление основного layout
        main_layout.addWidget(inputs_container)
        main_layout.addWidget(self.webEngine)

        # Установка пропорций
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 2)

        self.setLayout(layout)

    def add_parameter_row(self, label_text: str, widget: QWidget):
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label.setWordWrap(True)  # Перенос длинного текста
        label.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding,
            QSizePolicy.Policy.Fixed
        )

        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.inputs_widgets.addRow(label, widget)

    def closeEvent(self, event):
        file_operations.remove_dir(path=self.temppath[0])

    def run_model(self):
        pass

