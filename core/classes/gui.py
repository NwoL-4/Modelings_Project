import os
import sys
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QTextCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStatusBar, QLabel, QFormLayout, QMenuBar, QMenu, \
    QFrame, QPushButton, QScrollArea, QTextEdit

from core.classes.basic import LogLevel


class BasicGui(QWidget):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.setWindowTitle(self.name)
        self.setGeometry(300, 300, 400, 400)

        self.initUI()

    def initUI(self):
        mainLayout = QHBoxLayout()

        leftLayout = QVBoxLayout()

        self.inputs_layout = QFormLayout()
        self.status_bar = QStatusBar()
        self.logger = QLabel('')

        leftLayout.addLayout(self.inputs_layout)
        leftLayout.addWidget(self.status_bar)
        leftLayout.addWidget(self.logger)

        mainLayout.addLayout(leftLayout)

        self.setLayout(mainLayout)

        self._setup_menu()

    def add_widget(self, widget):
        self.inputs_layout.addWidget(widget)

    def add_row(self, label, widget):
        self.inputs_layout.addRow(label, widget)


    def _setup_menu(self):
        menubar = QMenuBar(self)

        model_menu = QMenu('Модель')

        model_reference = QAction(QIcon(''), 'Справка модели', self)
        model_reference.setShortcut('F2')
        model_reference.triggered.connect(self.reference_model)

        export_action = QAction(QIcon(''), 'Экспорт результатов', self)
        export_action.triggered.connect(self.export_results)

        exit_action = QAction(QIcon(''), 'Выход', self)
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.close)


        model_menu.addAction(model_reference)
        model_menu.addSeparator()
        model_menu.addAction(export_action)
        model_menu.addSeparator()
        model_menu.addAction(exit_action)

        view_menu = QMenu("Вид", self)

        toggle_logger = QAction(QIcon(''), 'Показать/Скрыть логгер', self)
        toggle_logger.setCheckable(True)
        toggle_logger.setChecked(True)
        toggle_logger.triggered.connect(self.toggle_logger_visibility)

        view_menu.addAction(toggle_logger)

        help_menu = QMenu("Справка", self)

        user_guide = QAction(QIcon(''), 'Руководство пользователя', self)
        user_guide.setShortcut('F1')
        user_guide.triggered.connect(self.show_user_guide)

        about_action = QAction(QIcon(''), 'О программе', self)
        about_action.triggered.connect(self.show_about)

        help_menu.addAction(user_guide)
        help_menu.addSeparator()
        help_menu.addAction(about_action)

        menubar.addMenu(model_menu)
        menubar.addMenu(view_menu)
        menubar.addMenu(help_menu)

        self.layout().setMenuBar(menubar)


    def reference_model(self):
        raise NotImplementedError('Неопределенный метод')

    def export_results(self):
        raise NotImplementedError('Неопределенный метод')

    def toggle_logger_visibility(self):
        raise NotImplementedError('Неопределенный метод')

    def show_user_guide(self):
        raise NotImplementedError('Неопределенный метод')

    def show_about(self):
        raise NotImplementedError('Неопределенный метод')


class ExpandableLogger(QWidget):
    """Расширяемый логгер с возможностью развертывания/сворачивания"""

    styles = {
        LogLevel.INFO: "color: #ffffff;",
        LogLevel.WARNING: "color: #ffd700;",
        LogLevel.ERROR: "color: #ff4444;",
        LogLevel.DEBUG: "color: #888888;",
        LogLevel.SUCCESS: "color: #ff0000;",
        LogLevel.DELETE: "color: #ff0000;",
        LogLevel.JS: "color: #ff0000;"
    }


    def __init__(self, parent=None, min_height=100, max_height=400):
        super().__init__(parent)
        self.min_height = min_height
        self.max_height = max_height
        self.current_height = self.min_height

        self.is_expanded = False

        self._setup_ui()
        self._settings_animations()
        self._connect_signals()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.frame = QFrame()
        self.frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        # TODO: Сделать загрузку css из assets.gui
        # self.frame.setStyleSheet()

        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(5, 5, 5, 5)

        self.expand_button = QPushButton()
        self.expand_button.setFixedSize(24, 24)
        self.expand_button.setStyleSheet()
        self._update_button_icon()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBar(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet()

        self.scroll_area.setWidget(self.log_text)
        self.frame_layout.addWidget(self.expand_button, 0, Qt.AlignmentFlag.AlignRight)
        self.frame_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.frame)

        self.setMinimumHeight(self.min_height)
        self.setMaximumHeight(self.max_height)

    def _settings_animations(self):
        self.animation_timer = QTimer()
        self.animation_timer.setInterval(100)
        self.animation_step = 5

    def _connect_signals(self):
        self.expand_button.clicked.connect(self.toggle_expansion)
        self.animation_timer.timeout.connect(self.animation_step)

    def _update_button_icon(self):
        icon_path = f"../icons/chevron_down.png" if self.is_expanded else "../icons/chevron_up.png"
        self.expand_button.setIcon(QIcon(icon_path))

    def _animate_expansion(self):
        target_height = self.max_height if self.is_expanded else self.min_height

        self.current_height = min(self.current_height + self.animation_step, target_height) if self.is_expanded else\
                              max(self.current_height - self.animation_step, target_height)

        self.setMaximumHeight(self.current_height)

        if self.current_height == target_height:
            self.animation_timer.stop()

    def toggle_expansion(self):
        self.is_expanded = not self.is_expanded
        self._update_button_icon()
        self.animation_timer.start()

    def add_message(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        formatted_message = f"[{timestamp}]---[{level}]: {message}"

        self.log_text.append(formatted_message)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        self.log_text.clear()

    def _get_level_style(self, level: str) -> str:
        return self.styles.get(level, self.styles[LogLevel.INFO])

    def export_logs(self):
        try:
            timestamp = datetime.now().strftime("%d:%m:%Y")

            path = os.path.join(sys.argv[0], "outputs", "logs", f"{timestamp}.log")
            with open(path, "w", encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            self.add_message("Лог успешно экспортирован")
        except Exception as e:
            print(e)
            self.add_message("Ошибка в экспорте логов", LogLevel.ERROR)
