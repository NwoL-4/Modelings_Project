import pandas as pd

from constants import ui_constants

css = f"""
    QWidget {{
        font-family: {ui_constants.MAIN_FONT};
        font-size: {ui_constants.FONT_SIZE}pt;
        background-color: {ui_constants.BACKGROUND_COLOR};  /* Фон окна */
        color: {ui_constants.TEXT_COLOR};  /* Цвет текста */
    }}
    QSpinBox {{
        height: {ui_constants.HEIGHT_SPINBOX}px;
        border-radius: {ui_constants.BORDER_RADIUS}px;
        background-color: {ui_constants.BACKGROUND_COLOR};  /* Фон редактируемых полей */
        border: {ui_constants.EDGE_WIDTH_BORDER} solid {ui_constants.COLOR_BORDER};  /* Окантовка полей */
    }}
    QLineEdit {{
        height: {ui_constants.HEIGHT_LINEEDIT}px;
        border-radius: {ui_constants.BORDER_RADIUS}px;
        background-color: {ui_constants.BACKGROUND_COLOR};  /* Фон редактируемых полей */
        border: {ui_constants.EDGE_WIDTH_BORDER} solid {ui_constants.COLOR_BORDER};  /* Окантовка полей */
    }}
    QPushButton {{
        height: {ui_constants.HEIGHT_PUSHBUTTON}px;
        border-radius: {ui_constants.BORDER_RADIUS}px;
        background-color: {ui_constants.BACKGROUND_COLOR};  /* Фон кнопок */
        border: {ui_constants.EDGE_WIDTH_BORDER} solid {ui_constants.COLOR_BORDER};  /* Окантовка кнопок */
        padding: {ui_constants.PADDING}px;
    }}
    QPushButton:hover {{
        color: {ui_constants.HOVER_COLOR};
    }}

    QTextEdit {{
        border: {ui_constants.EDGE_WIDTH_BORDER}px solid {ui_constants.COLOR_BORDER};
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
        /* border-right: {ui_constants.EDGE_WIDTH_BORDER} solid {ui_constants.COLOR_BORDER}; */
    }}
    
    QFormLayout {{
        spacing: 8px; /* Межстрочный интервал */
        margin-right: 2px; /* Учет полосы прокрутки */
    }}
    
    QTableView {{
        border: 1px solid #c0c0c0;
        gridline-color: #e0e0e0;
    }}
    QHeaderView::section {{
        padding: 4px 8px;
        background: #f8f8f8;
        border: none;
    }}
    QTableView::item {{
        padding: 2px 6px;
    }}
"""


def update_row_count(num_body: int, colors_body: list, model):
    new_row_count = num_body
    current_row_count = model.rowCount()

    new_data = pd.DataFrame(columns=model._data.columns)
    for i in range(min(current_row_count, new_row_count)):
        new_data.loc[i] = model._data.iloc[i]
    for i in range(current_row_count, new_row_count):
        new_data.loc[i] = ['0'] * len(model._data.columns)
        new_data.loc[i, 'Номер тела'] = i + 1
        new_data.loc[i, 'Цвет тела'] = colors_body[i]

    model._data = new_data
    model.layoutChanged.emit()
    return model