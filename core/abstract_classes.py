import os.path
import sys
from datetime import datetime

from PySide6.QtCore import QUrl, QSize, Qt, QAbstractTableModel, QModelIndex, QTimer
from PySide6.QtGui import QColor, QTextCursor, QIcon, QFont
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget, QTextEdit, QScrollArea, QLabel, QHBoxLayout, QPushButton, \
    QFormLayout, QSizePolicy, QTableView, QFrame, QHeaderView

import constants.ui_constants as ui_constants
import utils.file_operations
import utils.file_operations as file_operations
import utils.js_helpers as js_helpers
import utils.qt_helpers as qt_helpers


class LogLevel:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    SUCCESS = "SUCCESS"
    DELETE = "DELETE"


class ExpandableLogger(QWidget):
    """Расширяемый логгер с возможностью развертывания вверх"""

    def __init__(self, parent=None, min_height=100, max_height=400):
        super().__init__(parent)
        self.min_height = min_height
        self.max_height = max_height
        self.is_expanded = False

        self._setup_ui()
        self._setup_animations()
        self._connect_signals()

        # self.expand_button.click()

    def _setup_ui(self):
        """Инициализация UI компонентов"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Создаем основной фрейм
        self.frame = QFrame()
        self.frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.frame.setStyleSheet(qt_helpers.FORM_STYLE)

        # Layout для фрейма
        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(5, 5, 5, 5)

        # Кнопка развертывания
        self.expand_button = QPushButton()
        self.expand_button.setFixedSize(24, 24)
        self.expand_button.setStyleSheet(qt_helpers.EXPAND_BUTTON_STYLE)
        self._update_button_icon()

        # Область логов с прокруткой
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Текстовое поле для логов
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont(ui_constants.MAIN_FONT, ui_constants.FONT_SIZE))
        self.log_text.setStyleSheet(qt_helpers.LOGGER_STYLE)

        # Добавляем виджеты в layout
        self.scroll_area.setWidget(self.log_text)
        self.frame_layout.addWidget(self.expand_button, 0, Qt.AlignmentFlag.AlignRight)
        self.frame_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.frame)

        # Устанавливаем минимальный размер
        self.setMinimumHeight(self.min_height)
        self.setMaximumHeight(self.min_height)

    def _setup_animations(self):
        """Настройка анимации разворачивания"""
        self.animation_timer = QTimer()
        self.animation_timer.setInterval(10)  # 10ms для плавности
        self.animation_step = 5  # Шаг изменения высоты
        self.current_height = self.min_height

    def _connect_signals(self):
        """Подключение сигналов"""
        self.expand_button.clicked.connect(self.toggle_expansion)
        self.animation_timer.timeout.connect(self._animate_expansion)

    def _update_button_icon(self):
        """Обновление иконки кнопки развертывания"""
        icon_path = f"../icons/chevron_down.png" if self.is_expanded else "../icons/chevron_up.png"
        self.expand_button.setIcon(QIcon(icon_path))

    def _animate_expansion(self):
        """Анимация разворачивания/сворачивания"""
        target_height = self.max_height if self.is_expanded else self.min_height

        if self.is_expanded:
            self.current_height = min(self.current_height + self.animation_step, target_height)
        else:
            self.current_height = max(self.current_height - self.animation_step, target_height)

        self.setMaximumHeight(self.current_height)

        if self.current_height == target_height:
            self.animation_timer.stop()

    def toggle_expansion(self):
        """Переключение состояния развертывания"""
        self.is_expanded = not self.is_expanded
        self._update_button_icon()
        self.animation_timer.start()

    def log(self, message: str, level: str = "INFO"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"

        # Добавляем сообщение и прокручиваем вниз
        self.log_text.append(formatted_message)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        """Очистка лога"""
        self.log_text.clear()

    @staticmethod
    def _get_level_style(level: str) -> str:
        """Возвращает стиль для различных уровней логов"""
        styles = {
            LogLevel.INFO: "color: #ffffff;",
            LogLevel.WARNING: "color: #ffd700;",
            LogLevel.ERROR: "color: #ff4444;",
            LogLevel.DEBUG: "color: #888888;"
        }
        return styles.get(level, styles[LogLevel.INFO])

    def export_logs(self):
        """Экспорт логов в файл"""
        try:
            timestamp = datetime.now().strftime("%d:%m:%Y")

            path = os.path.join(sys.argv[0], 'logs')
            with open(os.path.join(path, f"{timestamp}_log.txt"), 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            self.log("Logs exported successfully", LogLevel.INFO)
        except Exception as e:
            self.log(f"Failed to export logs: {str(e)}", LogLevel.ERROR)


class ExpandingFormLayout(QFormLayout):
    def __init__(self):
        super().__init__()

    def addFullWidthWidget(self, widget):
        """Добавляет виджет на всю ширину формы"""
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.addRow(widget)


class WebViewWrapper(QWidget):
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
        table.setMinimumHeight(150)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        table.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Expanding)

        self.model = model

        table.setModel(self.model)

        table_layout = QVBoxLayout(self)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
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
        self.setStyleSheet(qt_helpers.MAIN_STYLE)

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
        self.webEngine = WebViewWrapper(path_to_html=self.temppath[1])

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

        self.logger = ExpandableLogger(min_height=100, max_height=200)

        bottom_layout.addWidget(self.runner, alignment=Qt.AlignmentFlag.AlignHCenter)
        bottom_layout.addWidget(self.logger)

        # Костыль на scroll_area
        widget = QWidget()
        self.inputs_widgets = ExpandingFormLayout()
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
        self.logger.export_logs()

    def run_model(self):
        pass

