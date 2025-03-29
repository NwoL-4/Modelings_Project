import pandas as pd

from constants import ui_constants

MAIN_STYLE = f"""
    QWidget {{
        font-family: {ui_constants.MAIN_FONT};
        font-size: {ui_constants.FONT_SIZE}pt;
        background-color: {ui_constants.BACKGROUND_COLOR};  /* Фон окна */
        color: {ui_constants.TEXT_COLOR};  /* Цвет текста */
    }}
    QSpinBox {{
        height: {ui_constants.SPINBOX_HEIGHT}px;
        border-radius: {ui_constants.BORDER_RADIUS}px;
        background-color: {ui_constants.BACKGROUND_COLOR};  /* Фон редактируемых полей */
        border: {ui_constants.BORDER_WIDTH_EDGE} solid {ui_constants.BORDER_COLOR};  /* Окантовка полей */
    }}
    QLineEdit {{
        height: {ui_constants.LINEEDIT_HEIGHT}px;
        border-radius: {ui_constants.BORDER_RADIUS}px;
        background-color: {ui_constants.BACKGROUND_COLOR};  /* Фон редактируемых полей */
        border: {ui_constants.BORDER_WIDTH_EDGE} solid {ui_constants.BORDER_COLOR};  /* Окантовка полей */
    }}
    QPushButton {{
        height: {ui_constants.PUSHBUTTON_HEIGHT}px;
        border-radius: {ui_constants.BORDER_RADIUS}px;
        background-color: {ui_constants.BACKGROUND_COLOR};  /* Фон кнопок */
        border: {ui_constants.BORDER_WIDTH_EDGE} solid {ui_constants.BORDER_COLOR};  /* Окантовка кнопок */
        padding: {ui_constants.PADDING}px;
    }}
    QPushButton:hover {{
        color: {ui_constants.HOVER_COLOR};
    }}
    
    QPushButton:pressed {{
        color: {ui_constants.HOVER_COLOR};
        background-color: {ui_constants.HOVER_COLOR};
    }}

    QTextEdit {{
        border: {ui_constants.BORDER_WIDTH_EDGE}px solid {ui_constants.BORDER_COLOR};
        border-radius: {ui_constants.BORDER_RADIUS}px;
        background: rgba(255, 255, 255, 0.9);
        selection-background-color: {ui_constants.HOVER_COLOR};
    }}
    
    QLineEdit, QSpinBox, QComboBox {{
        min-width: 200px;
        max-width: 300px;
    }}
    
    QLabel[class="param-label"] {{
        min-width: 150px;
        max-width: 200px;
        padding-right: 12px;
        /* border-right: {ui_constants.BORDER_WIDTH_EDGE} solid {ui_constants.BORDER_COLOR}; */
    }}
    
    QFormLayout {{
        spacing: 8px; /* Межстрочный интервал */
        margin-right: 2px; /* Учет полосы прокрутки */
    }}
    
    QTableView {{
        border: 0px solid #c0c0c0;
        gridline-color: {ui_constants.TEXT_COLOR};
    }}
    QHeaderView::section {{
        padding: 4px;
        background-color: {ui_constants.BACKGROUND_COLOR};
        border: 1px solid {ui_constants.BORDER_COLOR};
    }}
    QTableView::item {{
        padding: 2px 6px;
    }}
"""

LOGGER_STYLE = f"""
QTextEdit {{
    background-color: {ui_constants.LOGGER_BACKGROUND_COLOR};
    color: {ui_constants.TEXT_COLOR};
    border: none;
    }}
QScrollBar:vertical {{
    border: none;
    background: {ui_constants.BACKGROUND_COLOR};
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {ui_constants.BACKGROUND_COLOR};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


FORM_STYLE = f"""
QFrame {{
    background-color: {ui_constants.BACKGROUND_COLOR};
    border: 1px solid {ui_constants.LOGGER_BACKGROUND_COLOR};
    border-radius: 5px;
}}
"""

EXPAND_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    border: none;
    border-radius: {ui_constants.BORDER_RADIUS}px;
}}
QPushButton:hover {{
    background-color: {ui_constants.HOVER_COLOR};
}}
"""


INFOBOX_TEXT_STYLE = f"""
QLabel {{
    color: {ui_constants.TEXT_COLOR};
    font-size: {ui_constants.FONT_SIZE}px;
    font-family: {ui_constants.MAIN_FONT};
}}
"""

INFOBOX_STYLE = f"""
InfoPopup {{
    background-color: {ui_constants.LOGGER_BACKGROUND_COLOR};
    border-radius: {ui_constants.BORDER_RADIUS}px;
    min-width: {ui_constants.INFOBOX_MIN_WIDTH}px;
    max-width: {ui_constants.INFOBOX_MAX_WIDTH}px;
}}
"""


def update_row_count(num_body: int, colors_body: list, model):
    new_row_count = num_body
    current_row_count = model.rowCount()

    new_data = pd.DataFrame(columns=model.df.columns)
    for i in range(min(current_row_count, new_row_count)):
        new_data.loc[i] = model.df.iloc[i]
    for i in range(current_row_count, new_row_count):
        new_data.loc[i] = ['0'] * len(model.df.columns)
        new_data.loc[i, 'Номер тела'] = i + 1
        new_data.loc[i, 'Цвет тела'] = colors_body[i]

    model.df = new_data
    model.layoutChanged.emit()
    return model