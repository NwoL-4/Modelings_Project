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
    BORDER_WIDTH_EDGE,
    BORDER_COLOR,
    PADDING,
    HOVER_COLOR,
    DISABLE_COLOR,
    SPINBOX_HEIGHT,
    LINEEDIT_HEIGHT,
    PUSHBUTTON_HEIGHT
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
        'border width': BORDER_WIDTH_EDGE,
        'padding': PADDING,
        'border color': BORDER_COLOR,
        'hover color': HOVER_COLOR,
        'disable color': DISABLE_COLOR,
        'spinbox height': SPINBOX_HEIGHT,
        'lineedit height': LINEEDIT_HEIGHT,
        'pushbutton height': PUSHBUTTON_HEIGHT
    }


__all__ = ['ConstGroup']