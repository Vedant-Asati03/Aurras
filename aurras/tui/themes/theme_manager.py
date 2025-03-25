"""
Theme management system for Aurras TUI.
"""

from pathlib import Path
from typing import NamedTuple, Optional, Dict, Any
import uuid
from pydantic import BaseModel, Field
from rich.style import Style
from textual.app import InvalidThemeError
from textual.color import Color
from textual.theme import Theme as TextualTheme
from textual.widgets.text_area import TextAreaTheme
import yaml
import logging

log = logging.getLogger("aurras.themes")


class TextAreaSettings(BaseModel):
    """Styling to apply to TextAreas."""

    gutter: Optional[str] = Field(default=None)
    """The style to apply to the gutter."""

    cursor: Optional[str] = Field(default=None)
    """The style to apply to the cursor."""

    cursor_line: Optional[str] = Field(default=None)
    """The style to apply to the line the cursor is on."""

    cursor_line_gutter: Optional[str] = Field(default=None)
    """The style to apply to the gutter of the line the cursor is on."""

    matched_bracket: Optional[str] = Field(default=None)
    """The style to apply to bracket matching."""

    selection: Optional[str] = Field(default=None)
    """The style to apply to the selected text."""


class SyntaxTheme(BaseModel):
    """Colors used in highlighting syntax in text areas."""

    json_key: Optional[str] = None
    """The style to apply to JSON keys."""

    json_string: Optional[str] = None
    """The style to apply to JSON strings."""

    json_number: Optional[str] = None
    """The style to apply to JSON numbers."""

    json_boolean: Optional[str] = None
    """The style to apply to JSON booleans."""

    json_null: Optional[str] = None
    """The style to apply to JSON null values."""


class VariableStyles(BaseModel):
    """The style to apply to variables."""

    resolved: Optional[str] = None
    """The style to apply to resolved variables."""

    unresolved: Optional[str] = None
    """The style to apply to unresolved variables."""

    def fill_with_defaults(self, theme: "Theme") -> "VariableStyles":
        """Fill in missing values with defaults based on the theme."""
        return VariableStyles(
            resolved=self.resolved or f"bold {theme.primary}",
            unresolved=self.unresolved or f"bold {theme.error or '#ff0000'}",
        )


class UrlStyles(BaseModel):
    """The style to apply to URL input fields."""

    base: Optional[str] = None
    """The style to apply to the base URL."""

    protocol: Optional[str] = None
    """The style to apply to the protocol (e.g. http://)."""

    path: Optional[str] = None
    """The style to apply to the path part of the URL."""

    separator: Optional[str] = None
    """The style to apply to the separator (/) in the URL."""

    query: Optional[str] = None
    """The style to apply to the query part of the URL."""

    def fill_with_defaults(self, theme: "Theme") -> "UrlStyles":
        """Fill in missing values with defaults based on the theme."""
        return UrlStyles(
            base=self.base or theme.primary,
            protocol=self.protocol or theme.secondary or theme.primary,
            path=self.path or theme.accent or theme.primary,
            separator=self.separator or theme.secondary or theme.primary,
            query=self.query or theme.warning or theme.primary,
        )


class Theme(BaseModel):
    """A theme for the Aurras TUI."""

    name: str = Field(exclude=True)
    primary: str
    secondary: Optional[str] = None
    background: Optional[str] = None
    surface: Optional[str] = None
    panel: Optional[str] = None
    warning: Optional[str] = None
    error: Optional[str] = None
    success: Optional[str] = None
    accent: Optional[str] = None
    dark: bool = True

    text_area: TextAreaSettings = Field(default_factory=TextAreaSettings)
    """Styling to apply to TextAreas."""

    syntax: str | SyntaxTheme = Field(default="aurras", exclude=True)
    """The syntax highlighting theme to use. This can be a custom SyntaxTheme
    or a pre-defined Textual theme name such as monokai, dracula, github_light, or vscode_dark."""

    url: Optional[UrlStyles] = Field(default_factory=UrlStyles)
    """Styling to apply to URL input fields."""

    variable: Optional[VariableStyles] = Field(default_factory=VariableStyles)
    """Styling to apply to variables."""

    def to_textual_theme(self) -> TextualTheme:
        """Convert to a Textual theme."""
        theme_args = {
            "name": self.name,
            "primary": self.primary,
            "dark": self.dark,
        }

        if self.secondary:
            theme_args["secondary"] = self.secondary
        if self.background:
            theme_args["background"] = self.background
        if self.surface:
            theme_args["surface"] = self.surface
        if self.panel:
            theme_args["panel"] = self.panel
        if self.warning:
            theme_args["warning"] = self.warning
        if self.error:
            theme_args["error"] = self.error
        if self.success:
            theme_args["success"] = self.success
        if self.accent:
            theme_args["accent"] = self.accent

        variables: Dict[str, str] = {}

        # Add URL styling variables
        if self.url:
            url_styles = self.url.fill_with_defaults(self)
            variables.update(
                {
                    "url-base": url_styles.base,
                    "url-protocol": url_styles.protocol,
                    "url-path": url_styles.path,
                    "url-separator": url_styles.separator,
                    "url-query": url_styles.query,
                }
            )

        # Add variable styling variables
        if self.variable:
            var_styles = self.variable.fill_with_defaults(self)
            variables.update(
                {
                    "variable-resolved": var_styles.resolved,
                    "variable-unresolved": var_styles.unresolved,
                }
            )

        # Add text area styling variables
        if self.text_area:
            if self.text_area.gutter:
                variables["text-area-gutter"] = self.text_area.gutter
            if self.text_area.cursor:
                variables["text-area-cursor"] = self.text_area.cursor
            if self.text_area.cursor_line:
                variables["text-area-cursor-line"] = self.text_area.cursor_line
            if self.text_area.cursor_line_gutter:
                variables["text-area-cursor-line-gutter"] = (
                    self.text_area.cursor_line_gutter
                )
            if self.text_area.matched_bracket:
                variables["text-area-matched-bracket"] = self.text_area.matched_bracket
            if self.text_area.selection:
                variables["text-area-selection"] = self.text_area.selection

        # Add syntax highlighting variables
        if isinstance(self.syntax, SyntaxTheme):
            if self.syntax.json_key:
                variables["syntax-json-key"] = self.syntax.json_key
            if self.syntax.json_string:
                variables["syntax-json-string"] = self.syntax.json_string
            if self.syntax.json_number:
                variables["syntax-json-number"] = self.syntax.json_number
            if self.syntax.json_boolean:
                variables["syntax-json-boolean"] = self.syntax.json_boolean
            if self.syntax.json_null:
                variables["syntax-json-null"] = self.syntax.json_null

        if variables:
            theme_args["variables"] = variables

        return TextualTheme(**theme_args)

    @staticmethod
    def text_area_theme_from_theme_variables(
        theme_variables: Dict[str, str],
    ) -> TextAreaTheme:
        """Create a TextAreaTheme from theme variables."""
        variables = {
            k.replace("text-area-", ""): v
            for k, v in theme_variables.items()
            if k.startswith("text-area-")
        }
        syntax_styles = {}
        for key, value in theme_variables.items():
            if key.startswith("syntax-"):
                syntax_key = key.replace("syntax-", "")
                syntax_styles[syntax_key] = Style.parse(value)

        return TextAreaTheme(
            name=uuid.uuid4().hex,
            syntax_styles=syntax_styles,
            gutter_style=Style.parse(variables.get("gutter"))
            if "gutter" in variables
            else None,
            cursor_style=Style.parse(variables.get("cursor"))
            if "cursor" in variables
            else None,
            cursor_line_style=Style.parse(variables.get("cursor-line"))
            if "cursor-line" in variables
            else None,
            cursor_line_gutter_style=Style.parse(variables.get("cursor-line-gutter"))
            if "cursor-line-gutter" in variables
            else None,
            bracket_matching_style=Style.parse(variables.get("matched-bracket"))
            if "matched-bracket" in variables
            else None,
            selection_style=Style.parse(variables.get("selection"))
            if "selection" in variables
            else None,
        )


class UserThemeLoadResult(NamedTuple):
    """Result of loading user themes."""

    themes: Dict[str, TextualTheme]
    failures: list[tuple[Path, Exception]]


def load_user_themes(theme_dir: Path) -> UserThemeLoadResult:
    """Load user themes from a directory."""
    themes = {}
    failures = []

    if not theme_dir.exists():
        return UserThemeLoadResult(themes, failures)

    for path in theme_dir.glob("*.yaml"):
        try:
            theme = load_user_theme(path)
            if theme:
                themes[theme.name] = theme
        except Exception as e:
            failures.append((path, e))

    for path in theme_dir.glob("*.yml"):
        try:
            theme = load_user_theme(path)
            if theme:
                themes[theme.name] = theme
        except Exception as e:
            failures.append((path, e))

    return UserThemeLoadResult(themes, failures)


def load_user_theme(path: Path) -> Optional[TextualTheme]:
    """Load a user theme from a file."""
    if not path.exists():
        return None

    try:
        with open(path, "r") as f:
            theme_data = yaml.safe_load(f)
    except Exception as e:
        log.error(f"Error loading theme {path}: {e}")
        raise

    if not isinstance(theme_data, dict):
        raise ValueError(f"Theme file {path} must contain a YAML object")

    if "name" not in theme_data:
        raise ValueError(f"Theme file {path} must contain a 'name' field")

    try:
        theme = Theme(**theme_data)
        return theme.to_textual_theme()
    except Exception as e:
        log.error(f"Error parsing theme {path}: {e}")
        raise


# Define built-in themes

## Keep Galaxy theme (deep space-inspired theme with rich purples and blues)
galaxy_primary = Color.parse("#BD93F9")  # Vibrant purple
galaxy_secondary = Color.parse("#8BE9FD")  # Bright cyan
galaxy_warning = Color.parse("#FFB86C")  # Soft orange
galaxy_error = Color.parse("#FF5555")  # Bright red
galaxy_success = Color.parse("#50FA7B")  # Bright green
galaxy_accent = Color.parse("#FF79C6")  # Pink
galaxy_background = Color.parse("#282A36")  # Dark background
galaxy_surface = Color.parse("#383A59")  # Slightly lighter surface
galaxy_panel = Color.parse("#44475A")  # Panel color

## Keep Cyberpunk theme (neon on dark with high contrast)
cyberpunk_primary = Color.parse("#00F6FF")  # Bright cyan
cyberpunk_secondary = Color.parse("#BD00FF")  # Neon purple
cyberpunk_warning = Color.parse("#FFFC00")  # Bright yellow
cyberpunk_error = Color.parse("#FF3677")  # Hot pink
cyberpunk_success = Color.parse("#00FF9F")  # Neon green
cyberpunk_accent = Color.parse("#FF4DFD")  # Magenta
cyberpunk_background = Color.parse("#0A001A")  # Very dark purple
cyberpunk_surface = Color.parse("#150029")  # Dark purple
cyberpunk_panel = Color.parse("#200A33")  # Medium dark purple

## Add Noctura Contrast (Modern & Vibrant)
noctura_primary = Color.parse("#00A3FF")  # Vibrant Cyan
noctura_secondary = Color.parse("#FF8C00")  # Bright Orange
noctura_warning = Color.parse("#FFA500")  # Orange
noctura_error = Color.parse("#FF1744")  # Bright Red
noctura_success = Color.parse("#00C853")  # Lime Green
noctura_accent = Color.parse("#9C27B0")  # Deep Purple
noctura_background = Color.parse("#121212")  # Very Dark Gray
noctura_surface = Color.parse("#1E1E1E")  # Deep Gray
noctura_panel = Color.parse("#252525")  # Lighter Gray

## Add Cyber Night (Futuristic & Neon)
cybernight_primary = Color.parse("#0FF0FC")  # Neon Cyan
cybernight_secondary = Color.parse("#FF007A")  # Bright Pink
cybernight_warning = Color.parse("#FFB400")  # Neon Yellow
cybernight_error = Color.parse("#FF1744")  # Bright Red
cybernight_success = Color.parse("#39FF14")  # Electric Green
cybernight_accent = Color.parse("#892CDC")  # Vibrant Purple
cybernight_background = Color.parse("#0A0A0A")  # Almost Black
cybernight_surface = Color.parse("#151515")  # Dark Gray
cybernight_panel = Color.parse("#1B1B1B")  # Slightly lighter gray

## Add Midnight Rust (Muted & Professional)
midnight_rust_primary = Color.parse("#D97706")  # Deep Amber
midnight_rust_secondary = Color.parse("#BB2525")  # Rust Red
midnight_rust_warning = Color.parse("#F59E0B")  # Warm Orange
midnight_rust_error = Color.parse("#DC2626")  # Deep Red
midnight_rust_success = Color.parse("#22C55E")  # Muted Green
midnight_rust_accent = Color.parse("#8B5CF6")  # Soft Purple
midnight_rust_background = Color.parse("#181818")  # Charcoal Black
midnight_rust_surface = Color.parse("#222222")  # Dark Gray
midnight_rust_panel = Color.parse("#292929")  # Slightly lighter gray

## Add Eclipse Void (Minimal & Sleek)
eclipse_void_primary = Color.parse("#2196F3")  # Bright Blue
eclipse_void_secondary = Color.parse("#03DAC6")  # Teal
eclipse_void_warning = Color.parse("#FFB300")  # Golden Yellow
eclipse_void_error = Color.parse("#D32F2F")  # Crimson
eclipse_void_success = Color.parse("#4CAF50")  # Leaf Green
eclipse_void_accent = Color.parse("#8E24AA")  # Rich Purple
eclipse_void_background = Color.parse("#121212")  # Deep Black
eclipse_void_surface = Color.parse("#1A1A1A")  # Charcoal Gray
eclipse_void_panel = Color.parse("#252525")  # Lighter Gray

## Add Inferno Shadow (Fiery & Dramatic)
inferno_primary = Color.parse("#FF4500")  # Bright Orange
inferno_secondary = Color.parse("#FFD700")  # Gold
inferno_warning = Color.parse("#FFA500")  # Deep Orange
inferno_error = Color.parse("#FF1744")  # Blood Red
inferno_success = Color.parse("#66BB6A")  # Soft Green
inferno_accent = Color.parse("#D10000")  # Dark Red
inferno_background = Color.parse("#0A0A0A")  # Pure Black
inferno_surface = Color.parse("#161616")  # Charcoal Gray
inferno_panel = Color.parse("#222222")  # Slightly lighter gray

## Add Void Synthwave (Retro & Vibrant)
synthwave_primary = Color.parse("#FF007A")  # Neon Pink
synthwave_secondary = Color.parse("#5D00FF")  # Electric Purple
synthwave_warning = Color.parse("#FFC107")  # Golden Yellow
synthwave_error = Color.parse("#FF1744")  # Bright Red
synthwave_success = Color.parse("#00FF87")  # Neon Green
synthwave_accent = Color.parse("#00E5FF")  # Cyan
synthwave_background = Color.parse("#080808")  # Almost Black
synthwave_surface = Color.parse("#121212")  # Dark Gray
synthwave_panel = Color.parse("#1E1E1E")  # Slightly lighter gray

## Add Obsidian Frost (Cool & Icy)
obsidian_primary = Color.parse("#00BFFF")  # Deep Sky Blue
obsidian_secondary = Color.parse("#0077B6")  # Ocean Blue
obsidian_warning = Color.parse("#FBC02D")  # Light Gold
obsidian_error = Color.parse("#EF5350")  # Muted Red
obsidian_success = Color.parse("#81C784")  # Soft Green
obsidian_accent = Color.parse("#90CAF9")  # Frost Blue
obsidian_background = Color.parse("#0B0C10")  # Midnight Black
obsidian_surface = Color.parse("#1F2833")  # Dark Gray
obsidian_panel = Color.parse("#293845")  # Slightly lighter gray

# Update the BUILTIN_THEMES dictionary with the new themes
BUILTIN_THEMES: Dict[str, TextualTheme] = {
    "galaxy": TextualTheme(
        name="galaxy",
        primary=galaxy_primary.hex,
        secondary=galaxy_secondary.hex,
        warning=galaxy_warning.hex,
        error=galaxy_error.hex,
        success=galaxy_success.hex,
        accent=galaxy_accent.hex,
        background=galaxy_background.hex,
        surface=galaxy_surface.hex,
        panel=galaxy_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": galaxy_primary.hex,
            "input-selection-background": f"{galaxy_primary.hex} 35%",
            "footer-background": "transparent",
            "border-color": f"{galaxy_primary.hex} 30%",
            "text": "#F8F8F2",  # Bright text
            "text-muted": "#BFBFBF",  # Muted text
            "primary-background": "#373844",  # Slightly lighter than surface
            "primary-darken-1": galaxy_primary.darken(0.1).hex,
            "primary-darken-2": galaxy_primary.darken(0.2).hex,
            "selection": f"{galaxy_primary.hex} 30%",
        },
    ),
    "cyberpunk": TextualTheme(
        name="cyberpunk",
        primary=cyberpunk_primary.hex,
        secondary=cyberpunk_secondary.hex,
        warning=cyberpunk_warning.hex,
        error=cyberpunk_error.hex,
        success=cyberpunk_success.hex,
        accent=cyberpunk_accent.hex,
        background=cyberpunk_background.hex,
        surface=cyberpunk_surface.hex,
        panel=cyberpunk_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": cyberpunk_primary.hex,
            "input-selection-background": f"{cyberpunk_primary.hex} 35%",
            "footer-background": "transparent",
            "border-color": f"{cyberpunk_primary.hex} 30%",
            "text": "#EEFFFF",  # Bright cyan-white
            "text-muted": "#A2D6E9",  # Muted cyan
            "primary-background": "#1E0E30",  # Slightly lighter background
            "primary-darken-1": cyberpunk_primary.darken(0.1).hex,
            "primary-darken-2": cyberpunk_primary.darken(0.2).hex,
            "selection": f"{cyberpunk_secondary.hex} 50%",
        },
    ),
    # New theme: Noctura Contrast
    "noctura": TextualTheme(
        name="noctura",
        primary=noctura_primary.hex,
        secondary=noctura_secondary.hex,
        warning=noctura_warning.hex,
        error=noctura_error.hex,
        success=noctura_success.hex,
        accent=noctura_accent.hex,
        background=noctura_background.hex,
        surface=noctura_surface.hex,
        panel=noctura_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": noctura_primary.hex,
            "input-selection-background": f"{noctura_primary.hex} 35%",
            "footer-background": "transparent",
            "border-color": f"{noctura_primary.hex} 30%",
            "text": "#EAEAEA",  # Near-white text
            "text-muted": "#ABABAB",  # Muted white
            "primary-background": "#2A2A2A",  # Slightly lighter than surface
            "primary-darken-1": noctura_primary.darken(0.1).hex,
            "primary-darken-2": noctura_primary.darken(0.2).hex,
            "selection": f"{noctura_primary.hex} 30%",
        },
    ),
    # New theme: Cyber Night
    "cybernight": TextualTheme(
        name="cybernight",
        primary=cybernight_primary.hex,
        secondary=cybernight_secondary.hex,
        warning=cybernight_warning.hex,
        error=cybernight_error.hex,
        success=cybernight_success.hex,
        accent=cybernight_accent.hex,
        background=cybernight_background.hex,
        surface=cybernight_surface.hex,
        panel=cybernight_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": cybernight_primary.hex,
            "input-selection-background": f"{cybernight_primary.hex} 35%",
            "footer-background": "transparent",
            "border-color": f"{cybernight_primary.hex} 30%",
            "text": "#F5F5F5",  # Soft white
            "text-muted": "#A0A0A0",  # Medium gray
            "primary-background": "#1F1F1F",  # Slightly lighter than surface
            "primary-darken-1": cybernight_primary.darken(0.1).hex,
            "primary-darken-2": cybernight_primary.darken(0.2).hex,
            "selection": f"{cybernight_accent.hex} 40%",
        },
    ),
    # New theme: Midnight Rust
    "midnight_rust": TextualTheme(
        name="midnight_rust",
        primary=midnight_rust_primary.hex,
        secondary=midnight_rust_secondary.hex,
        warning=midnight_rust_warning.hex,
        error=midnight_rust_error.hex,
        success=midnight_rust_success.hex,
        accent=midnight_rust_accent.hex,
        background=midnight_rust_background.hex,
        surface=midnight_rust_surface.hex,
        panel=midnight_rust_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": midnight_rust_primary.hex,
            "input-selection-background": f"{midnight_rust_primary.hex} 35%",
            "footer-background": "transparent",
            "border-color": f"{midnight_rust_primary.hex} 30%",
            "text": "#E4E4E4",  # Soft white
            "text-muted": "#AAAAAA",  # Light gray
            "primary-background": "#262626",  # Slightly lighter than surface
            "primary-darken-1": midnight_rust_primary.darken(0.1).hex,
            "primary-darken-2": midnight_rust_primary.darken(0.2).hex,
            "selection": f"{midnight_rust_primary.hex} 30%",
        },
    ),
    # New theme: Eclipse Void
    "eclipse": TextualTheme(
        name="eclipse",
        primary=eclipse_void_primary.hex,
        secondary=eclipse_void_secondary.hex,
        warning=eclipse_void_warning.hex,
        error=eclipse_void_error.hex,
        success=eclipse_void_success.hex,
        accent=eclipse_void_accent.hex,
        background=eclipse_void_background.hex,
        surface=eclipse_void_surface.hex,
        panel=eclipse_void_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": eclipse_void_primary.hex,
            "input-selection-background": f"{eclipse_void_primary.hex} 35%",
            "footer-background": "transparent",
            "border-color": f"{eclipse_void_primary.hex} 30%",
            "text": "#E0E0E0",  # Soft white
            "text-muted": "#A0A0A0",  # Medium gray
            "primary-background": "#202020",  # Slightly lighter than surface
            "primary-darken-1": eclipse_void_primary.darken(0.1).hex,
            "primary-darken-2": eclipse_void_primary.darken(0.2).hex,
            "selection": f"{eclipse_void_primary.hex} 30%",
        },
    ),
    # New theme: Inferno Shadow
    "inferno": TextualTheme(
        name="inferno",
        primary=inferno_primary.hex,
        secondary=inferno_secondary.hex,
        warning=inferno_warning.hex,
        error=inferno_error.hex,
        success=inferno_success.hex,
        accent=inferno_accent.hex,
        background=inferno_background.hex,
        surface=inferno_surface.hex,
        panel=inferno_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": inferno_primary.hex,
            "input-selection-background": f"{inferno_primary.hex} 35%",
            "footer-background": "transparent",
            "border-color": f"{inferno_primary.hex} 30%",
            "text": "#F8F8F8",  # Soft white
            "text-muted": "#BBBBBB",  # Light gray
            "primary-background": "#1A1A1A",  # Slightly lighter than surface
            "primary-darken-1": inferno_primary.darken(0.1).hex,
            "primary-darken-2": inferno_primary.darken(0.2).hex,
            "selection": f"{inferno_secondary.hex} 30%",
            "boost": f"{inferno_primary.hex} 15%",  # Orange overlay
        },
    ),
    # New theme: Void Synthwave
    "synthwave": TextualTheme(
        name="synthwave",
        primary=synthwave_primary.hex,
        secondary=synthwave_secondary.hex,
        warning=synthwave_warning.hex,
        error=synthwave_error.hex,
        success=synthwave_success.hex,
        accent=synthwave_accent.hex,
        background=synthwave_background.hex,
        surface=synthwave_surface.hex,
        panel=synthwave_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": synthwave_primary.hex,
            "input-selection-background": f"{synthwave_primary.hex} 35%",
            "footer-background": "transparent",
            "border-color": f"{synthwave_primary.hex} 30%",
            "text": "#FFFFFF",  # Pure white
            "text-muted": "#B0B0B0",  # Medium gray
            "primary-background": "#161616",  # Slightly lighter than surface
            "primary-darken-1": synthwave_primary.darken(0.1).hex,
            "primary-darken-2": synthwave_primary.darken(0.2).hex,
            "selection": f"{synthwave_primary.hex} 30%",
            "boost": f"{synthwave_primary.hex} 20%",  # Pink overlay
        },
    ),
    # New theme: Obsidian Frost
    "obsidian": TextualTheme(
        name="obsidian",
        primary=obsidian_primary.hex,
        secondary=obsidian_secondary.hex,
        warning=obsidian_warning.hex,
        error=obsidian_error.hex,
        success=obsidian_success.hex,
        accent=obsidian_accent.hex,
        background=obsidian_background.hex,
        surface=obsidian_surface.hex,
        panel=obsidian_panel.hex,
        dark=True,
        variables={
            "input-cursor-background": obsidian_primary.hex,
            "input-selection-background": f"{obsidian_primary.hex} 35%",
            "footer-background": "transparent",
            "border-color": f"{obsidian_primary.hex} 30%",
            "text": "#E3F2FD",  # Soft ice blue
            "text-muted": "#A0C8E8",  # Muted blue
            "primary-background": "#2C3A47",  # Slightly lighter than surface
            "primary-darken-1": obsidian_primary.darken(0.1).hex,
            "primary-darken-2": obsidian_primary.darken(0.2).hex,
            "selection": f"{obsidian_primary.hex} 30%",
            "boost": f"{obsidian_primary.hex} 10%",  # Blue overlay
        },
    ),
}
