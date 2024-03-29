from typing import TypeVar

from titan._internal.preferences.components import Component as _Component
from titan._internal.preferences.widgets import (
    CheckBox,
    ColorPicker,
    ComboBox,
    Field,
    RadioButtons,
    Slider,
)

# TypeVar for the return type of from_component
PreferenceWidget = TypeVar(
    "PreferenceWidget", CheckBox, ColorPicker, ComboBox, Field, RadioButtons, Slider
)


def from_component(component: _Component) -> PreferenceWidget:
    """Return the appropriate widget for the given component.

    Args:
        component (Component): The component to create a widget for.
    """

    if component.type == component.Type.State:
        return CheckBox.from_component(component)
    elif component.type == component.Type.Color:
        return ColorPicker.from_component(component)
    elif component.type == component.Type.Combo:
        return ComboBox.from_component(component)
    elif component.type == component.Type.Field:
        return Field.from_component(component)
    elif component.type == component.Type.Radio:
        return RadioButtons.from_component(component)
    elif component.type == component.Type.Slider:
        return Slider.from_component(component)

    raise ValueError(f"Invalid component: {component}")


__all__ = (
    "CheckBox",
    "ColorPicker",
    "ComboBox",
    "Field",
    "RadioButton",
    "Slider",
    "from_component",
)
