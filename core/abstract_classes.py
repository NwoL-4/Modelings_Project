import os.path
import string
import sys
from datetime import datetime

import numpy as np
from PySide6.QtCore import QUrl, QSize, Qt, QAbstractTableModel, QModelIndex, QTimer, QPoint
from PySide6.QtGui import QColor, QTextCursor, QIcon, QFont, QPainter, QPainterPath, QPen, QAction
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget, QTextEdit, QScrollArea, QLabel, QHBoxLayout, QPushButton, \
    QFormLayout, QSizePolicy, QTableView, QFrame, QHeaderView, QApplication, QLineEdit, QSpinBox, QComboBox, QDialog, \
    QTextBrowser, QDialogButtonBox, QMenuBar, QMenu, QProgressBar

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
    JS = "JS"


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
            self.log("Логи успешно экспортированы", LogLevel.INFO)
        except Exception as e:
            self.log(f"Ошибка в экспорте логов: {str(e)}", LogLevel.ERROR)


class WebViewWrapper(QWidget):
    """ Кастомный WebView """
    def __init__(self, path_to_html, logger):
        super().__init__()

        self.path_to_html = path_to_html

        layout = QVBoxLayout()

        self.webView = QWebEngineView()
        self.channel = QWebChannel()
        self.bridge = js_helpers.PythonJsBridge(logger=logger)

        self.channel.registerObject("bridge", self.bridge)
        self.webView.page().setWebChannel(self.channel)

        profile = self.webView.page().profile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        settings = self.webView.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)

        self.load_initial_html()

        layout.addWidget(self.webView)

        self.setLayout(layout)

    def load_initial_html(self):
        with open(self.path_to_html, mode='w') as f:
            f.write(js_helpers.generate_html_code())

        self.webView.load(QUrl.fromLocalFile(self.path_to_html))


class SmartPandasModel(QAbstractTableModel):
    """ Кастомный TableModel на Pandas.DataFrame"""

    def __init__(self, data):
        super().__init__()
        self.df = data

    def rowCount(self, index=QModelIndex):
        return self.df.shape[0]

    def columnCount(self, parnet=QModelIndex):
        return self.df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                value = self.df.iloc[index.row(), index.column()]
                if isinstance(value, np.float64):
                    if np.isnan(value):
                        return str('-')
                return str(value)
            if role == Qt.ItemDataRole.BackgroundRole:
                if index.column() == 1:
                    color = self.df.iloc[index.row(), index.column()]
                    return QColor(color)
        return None

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            if any([symbol in string.ascii_letters for symbol in value]):
                float_value = np.nan
            else:
                float_value = np.float64(value.replace(',', '.'))

            self.df.iloc[index.row(), index.column()] = float_value
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.df.columns[col]

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEditable
        if index.column() in [0, 1]:
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable


class TableViewer(QWidget):
    """ Кастомный QTableView """
    def __init__(self, data):
        super().__init__()

        # Настройка основного виджета
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.model = SmartPandasModel(data)
        self.table = QTableView()
        self.table.setModel(self.model)

        # Настройка размеров таблицы
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # Настройка заголовков
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Настройка layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы
        layout.addWidget(self.table)

        # Обновляем размер при создании
        self.update_table_size()

    def update_table_size(self):
        """Обновляет размер таблицы под содержимое"""
        height = self.table.horizontalHeader().height() + 22
        for row in range(self.table.model().rowCount()):
            height += self.table.rowHeight(row)
        # Добавляем место для границ
        self.table.setFixedHeight(height + 5)
        self.setFixedHeight(height + 5)


class InfoPopup(QFrame):
    """Кастомное всплывающее окно с подсказкой"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Настройка внешнего вида
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Создаем layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        # Создаем и настраиваем label для текста
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setStyleSheet(qt_helpers.INFOBOX_TEXT_STYLE)

        layout.addWidget(self.label)

        # Настраиваем стиль фрейма
        self.setStyleSheet(qt_helpers.INFOBOX_STYLE)

    def setText(self, text):
        """Установка текста подсказки"""
        self.label.setText(text)

    def paintEvent(self, event):
        """Отрисовка тени и скругленных углов"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Создаем путь для скругленных углов
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 5, 5)

        # Рисуем тень
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(ui_constants.INFOBOX_SHADE_COLOR))
        painter.drawPath(path.translated(0, 1))

        # Рисуем основной фон
        painter.setBrush(QColor(ui_constants.INFOBOX_BG_COLOR))
        painter.drawPath(path)

        # Рисуем тонкую границу
        painter.setPen(QPen(QColor(ui_constants.INFOBOX_BORDER_COLOR), 1))
        painter.drawPath(path)


class HelpMixin:
    """Миксин для добавления всплывающей подсказки к виджетам"""

    def __init__(self, *args, help_text=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._help_text = help_text
        self._popup = None
        self._show_timer = QTimer()
        self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self._showPopup)
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._hidePopup)

    def setHelpText(self, text):
        """Установка текста подсказки"""
        self._help_text = text

    def enterEvent(self, event):
        """Обработка входа курсора в область виджета"""
        super().enterEvent(event)
        if self._help_text:
            self._show_timer.start(500)  # Показываем через 500мс

    def leaveEvent(self, event):
        """Обработка выхода курсора из области виджета"""
        super().leaveEvent(event)
        self._show_timer.stop()
        if self._popup:
            self._hide_timer.start(200)  # Скрываем через 200мс

    def _showPopup(self):
        """Показ всплывающего окна"""
        if not self._popup:
            self._popup = InfoPopup()
            self._popup.setText(self._help_text)

        # Позиционируем popup
        pos = self.mapToGlobal(QPoint(0, self.height()))
        screen_rect = QApplication.primaryScreen().geometry()

        # Проверяем, поместится ли popup снизу
        if pos.y() + self._popup.height() > screen_rect.height():
            pos.setY(pos.y() - self.height() - self._popup.height())

        # Проверяем, поместится ли popup справа
        if pos.x() + self._popup.width() > screen_rect.width():
            pos.setX(pos.x() - (pos.x() + self._popup.width() - screen_rect.width()))

        self._popup.move(pos)
        self._popup.show()

    def _hidePopup(self):
        """Скрытие всплывающего окна"""
        if self._popup:
            self._popup.hide()


class HelpLabel(HelpMixin, QLabel):
    pass


class HelpLineEdit(HelpMixin, QLineEdit):
    pass


class HelpComboBox(HelpMixin, QComboBox):
    pass


class HelpSpinBox(HelpMixin, QSpinBox):
    pass


class AboutDialog(QDialog):
    """Диалоговое окно с информацией о программе"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        # Создаем текстовый браузер для отображения информации
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)  # Разрешаем открывать внешние ссылки

        # HTML-разметка для красивого отображения
        about_text = f"""
        <div style="text-align: center;">
            <h2>Название программы</h2>
            <p style="font: {ui_constants.MAIN_FONT};
                      font-size: {ui_constants.FONT_SIZE}px;">Версия 0.1.0</p>
            <br>
            <p><b>Разработчик:</b> NwoL</p>
            <p><b>Email:</b> <a href="mailto:ImPerfect-18@yandex.ru">ImPerfect-18@yandex.ru</a></p>
            <p><b>GitHub:</b> <a href="https://github.com/NwoL-4">github.com/NwoL-4</a></p>
            <br>
            <p>© 2025 Все права защищены</p>
        </div>
        """
        text_browser.setHtml(about_text)

        # Добавляем кнопку закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)

        layout.addWidget(text_browser)
        layout.addWidget(button_box)


class HelpDialog(QDialog):
    """Диалоговое окно справки"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справка")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Создаем текстовый браузер для отображения справки
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)

        # HTML-разметка для справки
        help_text = """
        <h2>Руководство пользователя</h2>

        <h3>Содержание:</h3>
        <ol>
            <li><a href="#introduction">Введение</a></li>
            <li><a href="#getting-started">Начало работы</a></li>
            <li><a href="#features">Основные функции</a></li>
            <li><a href="#tips">Советы и подсказки</a></li>
        </ol>

        <h3 id="introduction">Введение</h3>
        <p>Здесь описание вашей программы и её назначение...</p>

        <h3 id="getting-started">Начало работы</h3>
        <p>Инструкции по началу работы с программой...</p>

        <h3 id="features">Основные функции</h3>
        <ul>
            <li>Функция 1 - описание...</li>
            <li>Функция 2 - описание...</li>
            <li>Функция 3 - описание...</li>
        </ul>

        <h3 id="tips">Советы и подсказки</h3>
        <p>Полезные советы по использованию программы...</p>
        """
        text_browser.setHtml(help_text)

        # Добавляем кнопку закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)

        layout.addWidget(text_browser)
        layout.addWidget(button_box)


class MainWidget(QWidget):
    """ Основной класс для визуализации любой модели"""

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

        scroll_area = QScrollArea()

        # Настройка растягивания компонентов
        inputs_layout.addWidget(scroll_area, 1)  # 100% доступного пространства

        # Контейнер для нижнего блока
        bottom_block = QWidget()
        bottom_layout = QVBoxLayout(bottom_block)
        bottom_layout.setContentsMargins(0, 10, 0, 0)  # Отступ сверху

        inputs_layout.addWidget(bottom_block, 0)  # Фиксированная высота

        self.runner = QPushButton('Запуск модели')
        self.runner.clicked.connect(self.run_model)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 1000)

        self.logger = ExpandableLogger(min_height=100, max_height=200)

        bottom_layout.addWidget(self.runner, alignment=Qt.AlignmentFlag.AlignHCenter)
        bottom_layout.addWidget(self.progressBar)
        bottom_layout.addWidget(self.logger)

        self.webEngine = WebViewWrapper(path_to_html=self.temppath[1],
                                        logger=self.logger)

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

        self.setup_menu()

    def add_parameter_row(self, label_text: str, widget: QWidget):
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label.setWordWrap(True)  # Перенос длинного текста

        widget.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Fixed
        )

        widget_container = QWidget()
        layout = QHBoxLayout(widget_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.inputs_widgets.addRow(label, widget)

    def setup_menu(self):
        """Настройка верхнего меню"""

        # Создаем меню бар
        menubar = QMenuBar(self)

        # Меню "Файл"
        model_menu = QMenu("Модель", self)

        # Действия для меню "Файл"
        model_reference = QAction(QIcon(""), "Справка модели", self)
        model_reference.setShortcut("F2")
        model_reference.triggered.connect(self.reference_model)

        export_action = QAction(QIcon("icons/export.png"), "Экспорт результатов...", self)
        export_action.triggered.connect(self.export_results)

        exit_action = QAction(QIcon("icons/exit.png"), "Выход", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)

        # Добавляем действия в меню "Файл"
        model_menu.addAction(model_reference)
        model_menu.addSeparator()
        model_menu.addAction(export_action)
        model_menu.addSeparator()
        model_menu.addAction(exit_action)

        # Меню "Вид"
        view_menu = QMenu("Вид", self)

        # Действия для меню "Вид"
        toggle_logger = QAction("Показать/скрыть логгер", self)
        toggle_logger.setCheckable(True)
        toggle_logger.setChecked(True)
        toggle_logger.triggered.connect(self.toggle_logger_visibility)

        # Добавляем действия в меню "Вид"
        view_menu.addAction(toggle_logger)

        # Меню "Справка"
        help_menu = QMenu("Справка", self)

        # Действия для меню "Справка"
        help_action = QAction(QIcon("icons/help.png"), "Руководство пользователя", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)

        about_action = QAction(QIcon("icons/about.png"), "О программе", self)
        about_action.triggered.connect(self.show_about)

        # Добавляем действия в меню "Справка"
        help_menu.addAction(help_action)
        help_menu.addSeparator()
        help_menu.addAction(about_action)

        # Добавляем все меню в меню бар
        menubar.addMenu(model_menu)
        menubar.addMenu(view_menu)
        menubar.addMenu(help_menu)

        # Устанавливаем меню бар
        self.layout().setMenuBar(menubar)

    def toggle_logger_visibility(self):
        """Переключение видимости логгера"""
        if self.logger.isVisible():
            self.logger.hide()
        else:
            self.logger.show()

    def show_help(self):
        """Показ справки"""
        help_dialog = HelpDialog(self)
        help_dialog.exec()

    def show_about(self):
        """Показ информации о программе"""
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def export_results(self):
        pass

    def reference_model(self):
        pass

    def closeEvent(self, event):
        self.logger.export_logs()
        file_operations.remove_dir(path=self.temppath[0])

    def add_frame(self, frame):
        pass

    def run_model(self):
        pass

    def init_fig(self):
        pass

    def create_frame(self):
        pass
