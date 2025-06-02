"""
Theme definitions for Aurras.

This module defines all the built-in themes available in Aurras.
Each theme is fully typed and provides a consistent structure for the application.
"""

import yaml
from typing import Dict, Final

from aurras.utils.logger import get_logger
from aurras.themes.colors import ThemeColor
from aurras.utils.path_manager import _path_manager
from aurras.themes.definitions import ThemeDefinition, ThemeCategory

logger = get_logger("aurras.themes.themes", log_to_console=False)


# Define the built-in themes with proper typing
GALAXY: Final[ThemeDefinition] = ThemeDefinition(
    name="GALAXY",
    display_name="Galaxy",
    description="Deep space-inspired theme with rich purples and blues",
    category=ThemeCategory.DARK,
    dark_mode=True,
    primary=ThemeColor("#BD93F9"),  # Vibrant purple
    secondary=ThemeColor("#8BE9FD"),  # Bright cyan
    accent=ThemeColor("#FF79C6"),  # Pink
    background=ThemeColor("#282A36"),  # Dark background
    surface=ThemeColor("#383A59"),  # Slightly lighter surface
    panel=ThemeColor("#44475A"),  # Panel color
    warning=ThemeColor("#FFB86C"),  # Soft orange
    error=ThemeColor("#FF5555"),  # Bright red
    success=ThemeColor("#50FA7B"),  # Bright green
    text=ThemeColor("#F8F8F2"),  # Light text
    text_muted=ThemeColor("#BFBFBF"),  # Muted text
    border=ThemeColor("#6272A4"),  # Border color
    title_gradient=["#BD93F9", "#B899FA", "#B39FFB", "#AEA5FC"],
    artist_gradient=[
        "#8BE9FD",
        "#8BE9FDAA",
        "#8BE9FD77",
        "#8BE9FD44",
    ],  # Added for consistency
    status_gradient=["#F8F8F2", "#F8F8F2AA", "#F8F8F277"],  # Added for consistency
    progress_gradient=[
        "#40FA70",
        "#45FA74",
        "#4AFA78",
        "#50FA7B",
        "#58FA81",
        "#60FA86",
        "#68FA8C",
        "#70FA91",
        "#78FA96",
        "#80FA9C",
        "#88FAA2",
        "#90FAA7",
        "#50FA7BAA",
    ],  # galaxy gradient
    feedback_gradient=["#50FA7B", "#50FA7BAA", "#50FA7B77"],  # Added for consistency
    history_gradient=[
        "#8BE9FD",
        "#8BE9FDAA",
        "#8BE9FD77",
        "#8BE9FD44",
    ],  # Added for consistency
    dim="#333366",
)

NEON: Final[ThemeDefinition] = ThemeDefinition(
    name="NEON",
    display_name="Neon",
    description="Vibrant digital visualization style",
    category=ThemeCategory.VIBRANT,
    dark_mode=True,
    primary=ThemeColor("#00FFFF"),  # Bright cyan
    secondary=ThemeColor("#FF00FF"),  # Magenta
    accent=ThemeColor("#39FF14"),  # Neon green
    success=ThemeColor("#39FF14"),  # Neon green
    warning=ThemeColor("#FFFF00"),  # Yellow
    error=ThemeColor("#FF3131"),  # Bright red
    text=ThemeColor("#FFFFFF"),  # White
    text_muted=ThemeColor("#CCCCCC"),  # Light grey
    title_gradient=["#FF00FF", "#FF33FF", "#FF66FF", "#FF99FF"],  # Pink gradient
    artist_gradient=["#00FFFF", "#33FFFF", "#66FFFF", "#99FFFF"],  # Cyan gradient
    status_gradient=["#FFFFFF", "#CCCCCC", "#999999"],  # White to gray
    progress_gradient=[
        "#4DFF00",
        "#46FF0A",
        "#3FFF14",
        "#39FF14",
        "#32FF24",
        "#29FF2F",
        "#21FF3B",
        "#1AFF4A",
        "#12FF57",
        "#0AFF64",
        "#05FF71",
        "#00FF7F",
    ],  # green to cyan
    feedback_gradient=["#FFFF00", "#FFCC00", "#FF9900"],  # Yellow to orange
    history_gradient=["#FF00FF", "#CC00FF", "#9900FF"],  # Magenta to purple
    dim="#333333",
)

VINTAGE: Final[ThemeDefinition] = ThemeDefinition(
    name="VINTAGE",
    display_name="Vintage",
    description="Warm retro vinyl player feel",
    category=ThemeCategory.RETRO,
    dark_mode=True,
    primary=ThemeColor("#CC9966"),  # Sepia
    secondary=ThemeColor("#FF9966"),  # Light orange
    accent=ThemeColor("#99CC66"),  # Olive green
    success=ThemeColor("#99CC66"),  # Olive green
    warning=ThemeColor("#FF9966"),  # Light orange
    error=ThemeColor("#CC3300"),  # Dark red
    text=ThemeColor("#FFCC99"),  # Light peach
    text_muted=ThemeColor("#CCCCCC"),  # Light gray
    title_gradient=["#CC9966", "#D9A978", "#E6BA8A", "#F2CB9C"],  # Sepia gradient
    artist_gradient=["#FFCC99", "#FFD6AD", "#FFE0C2", "#FFEBD6"],  # Peach gradient
    status_gradient=["#CCCCCC", "#BBBBBB", "#AAAAAA"],  # Light gray gradient
    progress_gradient=[
        "#88CC55",
        "#8FCE5B",
        "#96CC61",
        "#99CC66",
        "#9ECF6A",
        "#A3D16F",
        "#A7D475",
        "#AAD680",
        "#AFD98A",
        "#B4DB8F",
        "#B8DE94",
        "#BBE099",
        "#C0E3A1",
        "#C5E5A8",
    ],  # green to light green
    feedback_gradient=["#FF9966", "#FFAA77", "#FFBB88"],  # Orange gradient
    history_gradient=["#CC9966", "#BF8855", "#B37744"],  # Brown gradient
    dim="#332211",
)

MINIMAL: Final[ThemeDefinition] = ThemeDefinition(
    name="MINIMAL",
    display_name="Minimal",
    description="Clean distraction-free interface",
    category=ThemeCategory.MINIMAL,
    dark_mode=True,
    primary=ThemeColor("#FFFFFF"),  # White
    secondary=ThemeColor("#CCCCCC"),  # Light gray
    accent=ThemeColor("#AAFFAA"),  # Soft green
    success=ThemeColor("#AAFFAA"),  # Soft green
    warning=ThemeColor("#DDDDDD"),  # Very light gray
    error=ThemeColor("#FF5555"),  # Soft red
    text=ThemeColor("#FFFFFF"),  # White
    text_muted=ThemeColor("#BBBBBB"),  # Grey
    background=ThemeColor("#222222"),  # Very dark gray
    title_gradient=["#FFFFFF", "#F7F7F7", "#EFEFEF", "#E7E7E7"],  # White gradient
    artist_gradient=["#DDDDDD", "#D5D5D5", "#CDCDCD", "#C5C5C5"],  # Gray gradient
    status_gradient=["#BBBBBB", "#B3B3B3", "#AAAAAA"],  # Gray gradient
    progress_gradient=[
        "#9AFFA0",
        "#A0FFA5",
        "#A5FFAA",
        "#AAFFAA",
        "#AFFFAF",
        "#B3FFB3",
        "#B7FFB7",
        "#BBFFBB",
        "#BFFFBF",
        "#C4FFC4",
        "#C8FFC8",
        "#CCFFCC",
        "#D0FFD0",
        "#D5FFD5",
        "#D9FFD9",
    ],  # green gradient
    feedback_gradient=["#FFFFFF", "#F0F0F0", "#E0E0E0"],  # White to gray
    history_gradient=["#DDDDDD", "#D0D0D0", "#C3C3C3"],  # Gray gradient
    dim="#555555",
)

NIGHTCLUB: Final[ThemeDefinition] = ThemeDefinition(
    name="NIGHTCLUB",
    display_name="Night Club",
    description="Rich nightclub lighting inspired",
    category=ThemeCategory.VIBRANT,
    dark_mode=True,
    primary=ThemeColor("#8A2BE2"),  # Blue violet
    secondary=ThemeColor("#FF00FF"),  # Magenta
    accent=ThemeColor("#00FF7F"),  # Spring green
    success=ThemeColor("#00FF7F"),  # Spring green
    warning=ThemeColor("#FF00FF"),  # Magenta
    error=ThemeColor("#FF1493"),  # Deep pink
    text=ThemeColor("#FFFFFF"),  # White
    text_muted=ThemeColor("#B0B0B0"),  # Medium gray
    background=ThemeColor("#121212"),  # Very dark gray
    surface=ThemeColor("#1A1A1A"),  # Dark gray
    title_gradient=[
        "#FF00FF",
        "#E633FF",
        "#CC66FF",
        "#B299FF",
    ],  # Magenta to purple
    artist_gradient=["#00BFFF", "#33CCFF", "#66D9FF", "#99E6FF"],  # Blue gradient
    status_gradient=["#9370DB", "#A385E0", "#B39AE5", "#C3AFEA"],  # Purple gradient
    progress_gradient=[
        "#00E070",
        "#00E877",
        "#00F07D",
        "#00FF7F",
        "#0DFF85",
        "#1AFF8C",
        "#26FF93",
        "#33FF96",
        "#40FF9D",
        "#4DFFA5",
        "#5AFFAB",
        "#66FFAD",
        "#73FFB3",
        "#80FFB9",
        "#8CFFC0",
        "#99FFC4",
    ],  # green gradient
    feedback_gradient=["#FF1493", "#FF3DA1", "#FF66AF", "#FF8FBD"],  # Pink gradient
    history_gradient=[
        "#9370DB",
        "#7A5DCB",
        "#614ABB",
        "#4837AB",
    ],  # Purple gradient
    dim="#333366",
)

CYBERPUNK: Final[ThemeDefinition] = ThemeDefinition(
    name="CYBERPUNK",
    display_name="Cyberpunk",
    description="Bright futuristic cyberpunk aesthetic",
    category=ThemeCategory.FUTURISTIC,
    dark_mode=True,
    primary=ThemeColor("#00F3FF"),  # Bright cyan
    secondary=ThemeColor("#FF00DE"),  # Hot pink
    accent=ThemeColor("#FFFC00"),  # Bright yellow
    success=ThemeColor("#02FAF3"),  # Bright cyan
    warning=ThemeColor("#FFFC00"),  # Bright yellow
    error=ThemeColor("#FF00DE"),  # Hot pink
    text=ThemeColor("#EEFFFF"),  # Bright cyan-white
    text_muted=ThemeColor("#A2D6E9"),  # Muted cyan
    background=ThemeColor("#0A001A"),  # Very dark purple
    surface=ThemeColor("#150029"),  # Dark purple
    panel=ThemeColor("#200A33"),  # Medium dark purple
    title_gradient=["#FF00DE", "#FF33E5", "#FF66EC", "#FF99F2"],  # Pink gradient
    artist_gradient=["#00F3FF", "#33F5FF", "#66F7FF", "#99F9FF"],  # Cyan gradient
    status_gradient=["#FFFC00", "#FFFD3F", "#FFFE7F", "#FFFFBF"],  # Yellow gradient
    progress_gradient=[
        "#00FFFF",
        "#00F9FF",
        "#00F6FF",
        "#00F3FF",
        "#00E8FF",
        "#01DCFF",
        "#01D1FF",
        "#02C3FF",
        "#02B8FF",
        "#03ACFF",
        "#03A1FF",
        "#0496FF",
        "#048BFF",
        "#057BFF",
        "#056EFF",
        "#0060FF",
    ],  # cyan to blue gradient
    feedback_gradient=[
        "#FF00DE",
        "#C300FF",
        "#7800FF",
        "#1500FF",
    ],  # Pink to purple to blue
    history_gradient=[
        "#FFFC00",
        "#FFD000",
        "#FFA400",
        "#FF7800",
    ],  # Yellow to orange
    dim="#1B0033",  # Deep purple background
)

FOREST: Final[ThemeDefinition] = ThemeDefinition(
    name="FOREST",
    display_name="Forest",
    description="Earthy green natural environment",
    category=ThemeCategory.NATURAL,
    dark_mode=True,
    primary=ThemeColor("#4CAF50"),  # Forest green
    secondary=ThemeColor("#8BC34A"),  # Light green
    accent=ThemeColor("#CDDC39"),  # Lime
    success=ThemeColor("#4CAF50"),  # Forest green
    warning=ThemeColor("#FFC107"),  # Amber
    error=ThemeColor("#FF5722"),  # Deep orange
    text=ThemeColor("#FFFFFF"),  # White
    text_muted=ThemeColor("#DDDDDD"),  # Light gray
    background=ThemeColor("#1B2315"),  # Very dark green
    surface=ThemeColor("#2A3623"),  # Dark green
    panel=ThemeColor("#3A4733"),  # Medium dark green
    title_gradient=["#4CAF50", "#61B965", "#76C37A", "#8BCD8F"],  # Green gradient
    artist_gradient=[
        "#8BC34A",
        "#9CCC5E",
        "#ADD572",
        "#BEDE86",
    ],  # Light green gradient
    status_gradient=["#795548", "#8A6859", "#9B7B6A", "#AC8E7B"],  # Brown gradient
    progress_gradient=[
        "#C4D428",
        "#C8D730",
        "#CCDA35",
        "#CDDC39",
        "#CEDD3F",
        "#D0DF44",
        "#D1E04A",
        "#D3E04F",
        "#D4E155",
        "#D6E25A",
        "#D7E360",
        "#D9E465",
        "#DAE56B",
        "#DBE670",
        "#DDE776",
        "#DEE87B",
        "#E0E980",
    ],  # lime gradient
    feedback_gradient=[
        "#FF9800",
        "#FFA827",
        "#FFB84F",
        "#FFC777",
    ],  # Orange gradient
    history_gradient=[
        "#607D8B",
        "#738E9C",
        "#86A0AD",
        "#99B1BE",
    ],  # Blue-grey gradient
    dim="#2E3B2F",  # Dark forest background
)

OCEAN: Final[ThemeDefinition] = ThemeDefinition(
    name="OCEAN",
    display_name="Ocean",
    description="Calming blue oceanic color palette",
    category=ThemeCategory.NATURAL,
    dark_mode=True,
    primary=ThemeColor("#03A9F4"),  # Light blue
    secondary=ThemeColor("#00BCD4"),  # Cyan
    accent=ThemeColor("#009688"),  # Teal
    success=ThemeColor("#009688"),  # Teal
    warning=ThemeColor("#FFC107"),  # Amber
    error=ThemeColor("#F44336"),  # Red
    text=ThemeColor("#E3F2FD"),  # Very light blue
    text_muted=ThemeColor("#B3E5FC"),  # Light blue
    background=ThemeColor("#01323D"),  # Deep ocean blue
    surface=ThemeColor("#024558"),  # Dark blue
    panel=ThemeColor("#035670"),  # Medium blue
    title_gradient=["#03A9F4", "#33B8F6", "#66C6F8", "#99D5FA"],  # Blue gradient
    artist_gradient=["#00BCD4", "#33C7DB", "#66D2E2", "#99DDE9"],  # Cyan gradient
    status_gradient=[
        "#B2EBF2",
        "#C0EFF5",
        "#CEF3F7",
        "#DCF7FA",
    ],  # Light cyan gradient
    progress_gradient=[
        "#00877B",
        "#008F81",
        "#009286",
        "#009688",
        "#0D998C",
        "#1A9C90",
        "#279F96",
        "#33A59C",
        "#40A8A1",
        "#4DAEA6",
        "#59B1AB",
        "#66B5B0",
        "#73B8B5",
        "#80BCBA",
        "#8CBFBF",
        "#99C4C4",
        "#A5C8C8",
    ],  # teal gradient
    feedback_gradient=[
        "#4DD0E1",
        "#64D7E6",
        "#7BDEEB",
        "#92E6F0",
    ],  # Light blue gradient
    history_gradient=["#0288D1", "#0277BD", "#01579B", "#014377"],  # Darkening blue
    dim="#01323D",  # Deep ocean background
)

SUNSET: Final[ThemeDefinition] = ThemeDefinition(
    name="SUNSET",
    display_name="Sunset",
    description="Warm orange and pink sunset tones",
    category=ThemeCategory.NATURAL,
    dark_mode=True,
    primary=ThemeColor("#FF5722"),  # Deep orange
    secondary=ThemeColor("#FF9800"),  # Orange
    accent=ThemeColor("#FFC107"),  # Amber
    success=ThemeColor("#8BC34A"),  # Light green
    warning=ThemeColor("#FFC107"),  # Amber
    error=ThemeColor("#F44336"),  # Red
    text=ThemeColor("#FFFFFF"),  # White
    text_muted=ThemeColor("#FFE0B2"),  # Very light orange
    background=ThemeColor("#3E2723"),  # Dark brown
    surface=ThemeColor("#4E342E"),  # Medium brown
    panel=ThemeColor("#5D4037"),  # Light brown
    title_gradient=["#FF5722", "#FF7444", "#FF9166", "#FFAE88"],  # Orange gradient
    artist_gradient=[
        "#FF9800",
        "#FFA833",
        "#FFB866",
        "#FFC899",
    ],  # Light orange gradient
    status_gradient=["#FFC107", "#FFCB3F", "#FFD677", "#FFE0AF"],  # Amber gradient
    progress_gradient=[
        "#F43026",
        "#F4372E",
        "#F43F36",
        "#F44336",
        "#F4493D",
        "#F55246",
        "#F55B4E",
        "#F66356",
        "#F66C5E",
        "#F77366",
        "#F77C6E",
        "#F88376",
        "#F88C7E",
        "#F99386",
        "#F99C8E",
        "#FAA396",
        "#FAAC9E",
    ],  # red gradient
    feedback_gradient=["#E91E63", "#EE4B83", "#F377A2", "#F8A4C2"],  # Pink gradient
    history_gradient=[
        "#9C27B0",
        "#A952BD",
        "#B77CCA",
        "#C4A7D7",
    ],  # Purple gradient
    dim="#3E2723",  # Dark brown background
)

MONOCHROME: Final[ThemeDefinition] = ThemeDefinition(
    name="MONOCHROME",
    display_name="Monochrome",
    description="Classic black and white styling",
    category=ThemeCategory.MINIMAL,
    dark_mode=True,
    primary=ThemeColor("#FFFFFF"),  # White
    secondary=ThemeColor("#CCCCCC"),  # Light gray
    accent=ThemeColor("#666666"),  # Dark gray
    success=ThemeColor("#AAAAAA"),  # Medium gray
    warning=ThemeColor("#DDDDDD"),  # Very light gray
    error=ThemeColor("#999999"),  # Gray
    text=ThemeColor("#FFFFFF"),  # White
    text_muted=ThemeColor("#CCCCCC"),  # Light gray
    background=ThemeColor("#111111"),  # Very dark gray
    surface=ThemeColor("#222222"),  # Dark gray
    panel=ThemeColor("#333333"),  # Medium gray
    title_gradient=["#FFFFFF", "#E6E6E6", "#CCCCCC", "#B3B3B3"],  # White to gray
    artist_gradient=["#CCCCCC", "#BABABA", "#A8A8A8", "#969696"],  # Gray gradient
    status_gradient=["#999999", "#888888", "#777777", "#666666"],  # Gray gradient
    progress_gradient=[
        "#727272",
        "#6F6F6F",
        "#6C6C6C",
        "#696969",
        "#666666",
        "#636363",
        "#616161",
        "#5E5E5E",
        "#5B5B5B",
        "#595959",
        "#565656",
        "#535353",
        "#505050",
        "#4E4E4E",
        "#4B4B4B",
        "#494949",
        "#464646",
        "#444444",
        "#414141",
        "#3E3E3E",
        "#3B3B3B",
        "#393939",
        "#363636",
        "#333333",
    ],  # dark gray gradient
    feedback_gradient=["#FFFFFF", "#E0E0E0", "#C0C0C0", "#A0A0A0"],  # White to gray
    history_gradient=[
        "#333333",
        "#444444",
        "#555555",
        "#666666",
    ],  # Dark to light gray
    dim="#111111",  # Near black
)


# Default theme that will be used if no theme is specified in settings
DEFAULT_THEME: Final[str] = GALAXY.name
USER_THEME_CONFIG_FILE = _path_manager.config_dir / "themes.yaml"


def _load_user_themes() -> Dict[str, ThemeDefinition]:
    """
    Load all user-defined themes from the themes.yaml file.

    Returns:
        Dictionary of theme name to ThemeDefinition
    """
    user_themes = {}

    try:
        if not USER_THEME_CONFIG_FILE.exists():
            return user_themes

        with open(USER_THEME_CONFIG_FILE, "r") as f:
            themes_data: Dict = yaml.safe_load(f) or {}

        for theme_name, theme_properties in themes_data.items():
            try:
                theme_properties["name"] = theme_name.upper()
                theme_obj = ThemeDefinition.from_dict(theme_properties)

                user_themes[theme_obj.name] = theme_obj
                logger.debug(f"Loaded user theme: {theme_obj.name}")
            except Exception as e:
                logger.error(f"Failed to load theme '{theme_name}': {e}")

    except Exception as e:
        logger.error(f"Error loading user themes from {USER_THEME_CONFIG_FILE}: {e}")

    return user_themes


user_themes = _load_user_themes()

# Collection of all available themes with proper typing
AVAILABLE_THEMES: Final[Dict[str, ThemeDefinition]] = {
    GALAXY.name: GALAXY,
    NEON.name: NEON,
    VINTAGE.name: VINTAGE,
    MINIMAL.name: MINIMAL,
    NIGHTCLUB.name: NIGHTCLUB,
    CYBERPUNK.name: CYBERPUNK,
    FOREST.name: FOREST,
    OCEAN.name: OCEAN,
    SUNSET.name: SUNSET,
    MONOCHROME.name: MONOCHROME,
    **{theme_def.name: theme_def for theme_def in user_themes.values()},
}


def get_default_theme_from_settings() -> str:
    """
    Get the default theme from the settings.yaml file.

    Returns:
        The theme name specified in settings, or DEFAULT_THEME if not found
    """
    try:
        from aurras.core.settings import SETTINGS

        dafault_theme = SETTINGS.appearance_settings.theme

        theme_name = dafault_theme.upper()

        if theme_name in AVAILABLE_THEMES:
            return theme_name

        return DEFAULT_THEME

    except Exception as e:
        logger.error(f"Error getting theme from settings: {e}")

        return DEFAULT_THEME
