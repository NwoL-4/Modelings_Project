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

    def log(self, message: str, level: str = LogLevel.INFO):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        style = self._get_level_style(level)
        formatted_message = (f"<span style='{ui_constants.TEXT_COLOR};'>[{timestamp}]</span>\t"
                             f"<span style='{style};'>[{level}]</span>\t"
                             f"<span style='{style};'>{message}</span>\n")

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
            LogLevel.INFO: "color: #000000",
            LogLevel.WARNING: "color: #ffa420",
            LogLevel.ERROR: "color: #dc143c",
            LogLevel.DEBUG: "color: #db01ff",
            LogLevel.JS: "color: #1b00ff",
            LogLevel.SUCCESS: "color: #04ff01",
            LogLevel.DELETE: "color: #ff0000"
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