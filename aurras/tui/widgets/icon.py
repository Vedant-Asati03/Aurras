import enum


class Icon(enum.Enum):
    PRIMARY = "$primary"
    ACCENT = "$accent"
    SUCCESS = "$success"
    WARNING = "$warning"
    ERROR = "$error"
    SECONDARY = "$secondary"
    FOREGROUND = "$foreground"
    BACKGROUND = "$background"
    SURFACE = "$surface"
    PANEL = "$panel"
    BOOST = "$boost"
    TEXT_WARNING = "$text-warning"
    TEXT_ERROR = "$text-error"
    TEXT_SUCCESS = "$text-success"

    def __init__(self, value: str):
        self._value_ = value

    def __call__(self, icon: str, color=None):
        color = color or self.value
        return f"[{color}]{icon}[/{color}]"

    def __str__(self):
        return self.value
