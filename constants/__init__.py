"""
Константы для физичексой модели и интефейса
"""

from .physics_constants import (
    GRAVITATION_CONSTANT,
    SPEED_OF_LIGHT,
    SOLAR_MASS
)

from .ui_constants import (
    MAIN_FONT,
    FONT_SIZE,
    BACKGROUND_COLOR,
    TEXT_COLOR,
    BORDER_RADIUS,
    EDGE_WIDTH_BORDER,
    COLOR_BORDER,
    PADDING,
    HOVER_COLOR,
    DISABLE_COLOR,
    HEIGHT_SPINBOX,
    HEIGHT_LINEEDIT,
    HEIGHT_PUSHBUTTON
)

class ConstGroup:
    Physics = {
        'G': GRAVITATION_CONSTANT,
        'c': SPEED_OF_LIGHT,
        'SolarMass': SOLAR_MASS
    }

    UI = {
        'font': MAIN_FONT,
        'font size': FONT_SIZE,
        'text color': TEXT_COLOR,
        'background color': BACKGROUND_COLOR,
        'border radius': BORDER_RADIUS,
        'border width': EDGE_WIDTH_BORDER,
        'padding': PADDING,
        'border color': COLOR_BORDER,
        'hover color': HOVER_COLOR,
        'disable color': DISABLE_COLOR,
        'spinbox height': HEIGHT_SPINBOX,
        'lineedit height': HEIGHT_LINEEDIT,
        'pushbutton height': HEIGHT_PUSHBUTTON
    }


__all__ = ['ConstGroup']