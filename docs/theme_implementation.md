# Theme Implementation Documentation

This document provides a comprehensive overview of Aurras' sophisticated theme system architecture, explaining how the unified theme management works to deliver consistent styling across CLI and TUI interfaces.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Theme Flow](#theme-flow)
- [Adapter System](#adapter-system)
- [Color Management](#color-management)
- [Theme Definitions](#theme-definitions)
- [Integration Points](#integration-points)
- [Performance Optimizations](#performance-optimizations)
- [Code Examples](#code-examples)

## Architecture Overview

Aurras implements a **unified, adapter-based theme architecture** that seamlessly provides consistent styling across both CLI (Rich console) and TUI (Textual) interfaces. The system is designed around the principle of **single source of truth**, where one theme definition drives styling for all UI components.

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│              (CLI Commands, TUI Screens)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Theme Manager                                │
│          (get_theme, set_current_theme)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
            ┌─────────┴─────────┐
            │                   │
┌───────────▼──────────┐ ┌──────▼──────────────────┐
│   Rich Adapter       │ │ Textual Adapter         │
│(theme_to_rich_theme) │ │(theme_to_textual_theme) │
└───────────┬──────────┘ └──────┬──────────────────┘
            │                   │
┌───────────▼──────────┐ ┌──────▼──────────┐
│   Rich Console       │ │   Textual App   │
│     Styling          │ │     Styling     │
└──────────────────────┘ └─────────────────┘
```

## Core Components

### 1. ThemeDefinition (Core Data Structure)

**Location**: `aurras/themes/definitions.py`

The `ThemeDefinition` class serves as the central data structure that defines all theme properties. It provides a comprehensive color palette and metadata for consistent application styling.

**Key Responsibilities**:
- Defining comprehensive color palettes
- Managing theme metadata and categorization
- Providing validation and normalization
- Supporting extensibility through custom fields

**Interface**:
```python
@dataclass
class ThemeDefinition:
    # Metadata
    name: str
    display_name: str
    description: str = ""
    category: ThemeCategory = ThemeCategory.CUSTOM
    dark_mode: bool = True

    # Core colors
    primary: Optional[ThemeColor] = None
    secondary: Optional[ThemeColor] = None
    accent: Optional[ThemeColor] = None

    # UI background colors
    background: Optional[ThemeColor] = None
    surface: Optional[ThemeColor] = None
    panel: Optional[ThemeColor] = None

    # Status colors
    warning: Optional[ThemeColor] = None
    error: Optional[ThemeColor] = None
    success: Optional[ThemeColor] = None
    info: Optional[ThemeColor] = None

    # Text colors
    text: Optional[ThemeColor] = None
    text_muted: Optional[ThemeColor] = None
    border: Optional[ThemeColor] = None

    # Gradients for enhanced visuals
    title_gradient: Optional[List[str]] = None
    artist_gradient: Optional[List[str]] = None
    status_gradient: Optional[List[str]] = None
    progress_gradient: Optional[List[str]] = None
    feedback_gradient: Optional[List[str]] = None
    history_gradient: Optional[List[str]] = None
```

### 2. Theme Manager

**Location**: `aurras/themes/manager.py`

The theme manager provides the central API for theme operations throughout the application.

**Key Functions**:
- **Theme Retrieval**: Get themes by name or current theme
- **Theme Switching**: Set current theme with validation
- **Theme Discovery**: Find and load user-defined themes
- **File Operations**: Load and save themes to/from JSON files

### 3. ThemeColor (Color Abstraction)

**Location**: `aurras/themes/colors.py`

The `ThemeColor` class provides a rich color abstraction with support for transformations and gradients.

**Features**:
- **Hex Color Management**: Validates and normalizes hex color values
- **Color Transformations**: Darken, lighten, and alpha adjustments
- **Gradient Generation**: Automatic gradient creation
- **Format Conversion**: RGB, HSV, and hex conversions

## Theme Flow

The theme system follows a **centralized configuration workflow** that ensures consistency across all UI components:

### Stage 1: Theme Selection
```
User Input → Theme Validation → Theme Manager → Current Theme Update
```

### Stage 2: Adapter Conversion
```
ThemeDefinition → Rich Adapter → Rich Theme Objects
                → Textual Adapter → Textual Theme Objects
```

### Stage 3: UI Application
```
Rich Theme → Console Styling → CLI Interface
Textual Theme → App Styling → TUI Interface
```

### Stage 4: Live Updates
```
Theme Change → Adapter Refresh → UI Re-rendering → Instant Visual Update
```

## Adapter System

The adapter system enables the unified theme definitions to work with different UI frameworks while maintaining consistency.

### RichAdapter

**Location**: `aurras/themes/adapters/rich_adapter.py`

Converts theme definitions to Rich library compatible formats for CLI interfaces.

**Features**:
- **Style Mapping**: Maps theme colors to Rich style definitions
- **Gradient Support**: Converts gradients to Rich-compatible formats
- **Caching**: Performance optimization through intelligent caching
- **Fallback Handling**: Graceful degradation with sensible defaults

**Conversion Process**:
1. Extract colors from ThemeDefinition
2. Map to Rich style names with fallbacks
3. Create Rich Theme object with computed styles
4. Cache result for performance optimization

**Style Mappings**:
```python
style_mapping = {
    "primary": (theme_def.primary.hex, [], "#FFFFFF"),
    "secondary": (theme_def.secondary.hex, [fallback1], "#CCCCCC"),
    "accent": (theme_def.accent.hex, [fallback1, fallback2], "#AAAAAA"),
    "success": (theme_def.success.hex, [fallback1], "#00FF00"),
    "warning": (theme_def.warning.hex, [], "#FFCC00"),
    "error": (theme_def.error.hex, [], "#FF0000"),
}
```

### TextualAdapter

**Location**: `aurras/themes/adapters/textual_adapter.py`

Converts theme definitions to Textual library compatible formats for TUI interfaces.

**Features**:
- **Textual Theme Creation**: Builds Textual Theme objects
- **Variable System**: Supports Textual's CSS variable system
- **Text Area Themes**: Specialized themes for code editors
- **Component Styling**: Maps theme colors to Textual components

**Key Methods**:
```python
def theme_to_textual_theme(theme_def: ThemeDefinition) -> TextualTheme:
    """Convert ThemeDefinition to Textual Theme."""

def theme_to_text_area_theme(theme_def: ThemeDefinition) -> TextAreaTheme:
    """Create TextAreaTheme for code editors."""

def theme_to_textual_variables(theme_def: ThemeDefinition) -> Dict[str, str]:
    """Generate CSS variables from theme."""
```

## Color Management

### ThemeColor Class

**Location**: `aurras/themes/colors.py`

Advanced color management with support for transformations and validations.

**Core Features**:
- **Validation**: Ensures valid hex color formats
- **Normalization**: Standardizes color representations
- **Transformations**: Darken, lighten, and alpha operations
- **Gradient Generation**: Automatic gradient creation

**Color Operations**:
```python
# Color transformations
primary = ThemeColor("#FF5733")
darker = primary.darken(0.2)      # "#CC451F"
lighter = primary.lighten(0.1)    # "#FF6B4D"
with_alpha = primary.with_alpha(50)  # "#FF5733 50%"

# Gradient generation
gradient = primary.generate_gradient(steps=4)
# ["#FF5733", "#FF6B4D", "#FF7F66", "#FF9380"]
```

### ColorTriplet

**Location**: `aurras/themes/colors.py`

RGB color representation with validation and conversion utilities.

**Features**:
- **RGB Validation**: Ensures components are within 0-255 range
- **Hex Conversion**: Bidirectional hex string conversion
- **Immutable Design**: Thread-safe color representation

### Color Utilities

**Location**: `aurras/themes/utils.py`

Comprehensive color utility functions for various operations.

**Utility Functions**:
```python
def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex string."""

def is_light_color(hex_color: str) -> bool:
    """Determine if a color is light or dark."""

def validate_hex_color(hex_color: str) -> bool:
    """Validate hex color format."""
```

## Theme Definitions

### Built-in Theme Collection

**Location**: `aurras/themes/themes.py`

Aurras ships with a carefully curated collection of 10 built-in themes across different categories.

**Theme Categories**:
- **Dark Themes**: Galaxy, Neon, Cyberpunk, Forest, Ocean
- **Light Themes**: Vintage, Minimal
- **Vibrant Themes**: Nightclub, Sunset
- **Minimal Themes**: Monochrome

**Example Theme Definition**:
```python
GALAXY: Final[ThemeDefinition] = ThemeDefinition(
    name="GALAXY",
    display_name="Galaxy",
    description="Deep space-inspired theme with rich purples and blues",
    category=ThemeCategory.DARK,
    dark_mode=True,
    primary=ThemeColor("#BD93F9"),      # Vibrant purple
    secondary=ThemeColor("#8BE9FD"),    # Bright cyan
    accent=ThemeColor("#FF79C6"),       # Pink
    background=ThemeColor("#282A36"),   # Dark background
    surface=ThemeColor("#383A59"),      # Slightly lighter surface
    panel=ThemeColor("#44475A"),        # Panel color
    warning=ThemeColor("#FFB86C"),      # Soft orange
    error=ThemeColor("#FF5555"),        # Bright red
    success=ThemeColor("#50FA7B"),      # Bright green
    text=ThemeColor("#F8F8F2"),         # Light text
    text_muted=ThemeColor("#BFBFBF"),   # Muted text
    border=ThemeColor("#6272A4"),       # Border color
    title_gradient=["#BD93F9", "#B899FA", "#B39FFB", "#AEA5FC"],
    progress_gradient=[
        "#40FA70", "#45FA74", "#4AFA78", "#50FA7B",
        "#58FA81", "#60FA86", "#68FA8C", "#70FA91"
    ],
    dim="#333366",
)
```

### Theme Categories

**Location**: `aurras/themes/definitions.py`

Themes are organized into logical categories for better organization and discovery.

```python
class ThemeCategory(Enum):
    DARK = auto()          # Dark mode themes
    LIGHT = auto()         # Light mode themes  
    VIBRANT = auto()       # High contrast, colorful themes
    MINIMAL = auto()       # Clean, distraction-free themes
    RETRO = auto()         # Vintage, nostalgic themes
    NATURAL = auto()       # Nature-inspired themes
    FUTURISTIC = auto()    # Sci-fi, cyberpunk themes
    CUSTOM = auto()        # User-defined themes
```

### User Theme Support

The system supports loading custom user themes from JSON files.

**User Theme Directory**: `~/.aurras/themes/`

**Theme File Format**:
```json
{
  "name": "MY_CUSTOM_THEME",
  "display_name": "My Custom Theme",
  "description": "A personalized theme",
  "category": "CUSTOM",
  "dark_mode": true,
  "colors": {
    "primary": {"hex": "#FF5733"},
    "secondary": {"hex": "#33C3FF"},
    "accent": {"hex": "#FFD700"}
  },
  "gradients": {
    "title_gradient": ["#FF5733", "#FF6B4D", "#FF7F66"],
    "progress_gradient": ["#33C3FF", "#4DD0E1", "#80DEEA"]
  }
}
```

## Integration Points

### CLI Integration

**Location**: `aurras/utils/console/manager.py`

The theme system integrates with the CLI through the `ThemedConsole` class.

**Features**:
- **Themed Console**: Automatically styled Rich console
- **Live Theme Switching**: Change themes without restart
- **Gradient Text**: Apply theme gradients to text
- **Style Mapping**: Automatic color mapping for UI elements

**Integration Process**:
1. **Console Creation**: Initialize themed console with current theme
2. **Style Application**: Apply Rich theme to console
3. **Theme Updates**: Live theme switching updates console
4. **Gradient Rendering**: Apply color gradients to text elements

### TUI Integration

**Location**: `aurras/tui/app.py`, `aurras/tui/themes/theme_manager.py`

The TUI system uses the unified theme definitions converted to Textual-compatible formats.

**Integration Components**:
- **Theme Loading**: Load and register themes at app startup
- **Live Switching**: Change themes without app restart
- **CSS Variables**: Generate CSS variables from theme colors
- **Component Styling**: Style TUI widgets with theme colors

**TUI Theme Process**:
1. **App Initialization**: Load all available themes
2. **Theme Registration**: Register themes with Textual app
3. **Current Theme Setting**: Set initial theme from settings
4. **Live Updates**: Switch themes dynamically through settings

### Settings Integration

**Location**: `aurras/core/settings/updater.py`, `aurras/utils/command/processors/theme.py`

Themes integrate with the settings system for persistence and management.

**Features**:
- **Theme Persistence**: Save current theme to settings
- **Settings Sync**: Automatic theme loading from settings
- **Theme Commands**: CLI commands for theme management
- **Live Updates**: Settings changes trigger theme updates

**Command Integration**:
```bash
# List available themes
aurras theme list

# Set current theme
aurras theme set galaxy

# Display current theme
aurras theme current

# Preview theme (TUI only)
aurras theme preview neon
```

### Player Integration

**Location**: `aurras/player/` (various components)

The media player interface uses themed styling for consistent appearance.

**Styled Components**:
- **Now Playing Display**: Uses primary and accent colors
- **Progress Bars**: Applies progress gradient colors
- **Status Messages**: Uses status color palette
- **Queue Display**: Themed list rendering

## Performance Optimizations

### 1. Intelligent Caching

The theme system implements multi-level caching for optimal performance.

**Adapter Caching**:
```python
# Rich theme cache
_rich_theme_cache = ThemeValueCache[str, RichTheme]()

# Gradient cache  
_gradient_cache = ThemeValueCache[str, Dict[str, List[str]]]()

# Usage with automatic caching
def theme_to_rich_theme(theme_def: ThemeDefinition) -> RichTheme:
    return _rich_theme_cache.get(theme_def.name, _compute_rich_theme, theme_def)
```

**Cache Benefits**:
- **Reduced Computation**: Avoid recomputing theme conversions
- **Memory Efficiency**: LRU eviction of unused themes
- **Performance**: Sub-millisecond theme switching

### 2. Lazy Loading

Themes are loaded on-demand to minimize startup time.

**On-Demand Loading**:
- **Theme Files**: Load user themes only when needed
- **Adapter Conversion**: Convert themes only when used
- **Gradient Computation**: Generate gradients on first use

### 3. Color Optimization

**Pre-computed Values**:
- **Color Triplets**: RGB values computed once during initialization
- **Gradient Caching**: Expensive gradient calculations cached
- **Validation**: Color validation performed once at creation

### 4. Thread Safety

The theme system is designed to be thread-safe for concurrent access.

**Thread-Safe Components**:
- **Immutable Theme Definitions**: Thread-safe by design
- **Cached Values**: Thread-safe cache implementations
- **Atomic Updates**: Theme switching uses atomic operations

## Code Examples

### Basic Theme Usage

```python
from aurras.themes import get_theme, set_current_theme, get_available_themes

# Get current theme
current_theme = get_theme()
print(f"Using theme: {current_theme.display_name}")

# List available themes
themes = get_available_themes()
for theme_name in themes:
    theme = get_theme(theme_name)
    print(f"{theme.display_name}: {theme.description}")

# Switch theme
success = set_current_theme("NEON")
if success:
    print("Theme switched successfully")
```

### Creating Custom Themes

```python
from aurras.themes import ThemeDefinition, ThemeColor, ThemeCategory

# Create custom theme
custom_theme = ThemeDefinition(
    name="MY_THEME",
    display_name="My Custom Theme",
    description="A personalized theme",
    category=ThemeCategory.CUSTOM,
    dark_mode=True,
    primary=ThemeColor("#FF5733"),
    secondary=ThemeColor("#33C3FF"),
    accent=ThemeColor("#FFD700"),
    background=ThemeColor("#1A1A1A"),
    text=ThemeColor("#FFFFFF"),
    title_gradient=["#FF5733", "#FF6B4D", "#FF7F66"],
)

# Save theme to file
from aurras.themes import save_theme_to_file
save_theme_to_file(custom_theme, "~/.aurras/themes/my_theme.json")
```

### Rich Console Integration

```python
from aurras.themes.adapters import theme_to_rich_theme
from aurras.themes import get_theme
from rich.console import Console

# Get themed console
theme = get_theme("GALAXY")
rich_theme = theme_to_rich_theme(theme)
console = Console(theme=rich_theme)

# Use themed styling
console.print("Primary text", style="primary")
console.print("Success message", style="success")
console.print("Error message", style="error")

# Apply gradients
from aurras.utils.console.manager import apply_gradient_to_text
gradient_text = apply_gradient_to_text(
    "Beautiful Gradient Text", 
    theme.title_gradient
)
console.print(gradient_text)
```

### Textual TUI Integration

```python
from aurras.themes.adapters import theme_to_textual_theme
from aurras.themes import get_theme
from textual.app import App

class MyApp(App):
    def __init__(self):
        super().__init__()
        
        # Apply theme
        theme = get_theme("CYBERPUNK")
        textual_theme = theme_to_textual_theme(theme)
        self.theme = textual_theme.name
        self.register_theme(textual_theme)
    
    def switch_theme(self, theme_name: str):
        """Switch theme dynamically."""
        theme = get_theme(theme_name)
        textual_theme = theme_to_textual_theme(theme)
        self.register_theme(textual_theme)
        self.theme = textual_theme.name
```

### Color Manipulation

```python
from aurras.themes.colors import ThemeColor

# Create and manipulate colors
primary = ThemeColor("#BD93F9")

# Color transformations
darker = primary.darken(0.2)      # More subtle color
lighter = primary.lighten(0.15)   # Brighter variant
semi_transparent = primary.with_alpha(70)  # 70% opacity

# Generate gradient
gradient = primary.generate_gradient(steps=5)
print(gradient)
# ['#BD93F9', '#C8A6FA', '#D3B9FB', '#DECCFC', '#E9DFFD']

# Create from different color spaces
from_rgb = ThemeColor.from_rgb(189, 147, 249)
from_hsv = ThemeColor.from_hsv(0.7, 0.4, 0.98)
```

### Theme Discovery and Management

```python
from aurras.themes.manager import (
    discover_user_themes, 
    get_themes_by_category,
    register_user_theme
)

# Discover user themes
user_themes = discover_user_themes("~/.aurras/themes/")
for theme in user_themes:
    register_user_theme(theme)
    print(f"Loaded user theme: {theme.display_name}")

# Get themes by category
dark_themes = get_themes_by_category("DARK")
minimal_themes = get_themes_by_category("MINIMAL")

# Theme filtering
vibrant_themes = {
    name: theme for name, theme in dark_themes.items() 
    if theme.category == ThemeCategory.VIBRANT
}
```

### Advanced Adapter Usage

```python
from aurras.themes.adapters.rich_adapter import (
    get_gradient_styles, 
    create_rich_style_from_color
)

# Get gradient styles for Rich
theme = get_theme("OCEAN")
gradient_styles = get_gradient_styles(theme)

# Create custom Rich style
color = ThemeColor("#03A9F4")
rich_style = create_rich_style_from_color(color, bold=True)

# Apply to console
console.print("Styled text", style=rich_style)
```

---

## Summary

The Aurras theme implementation represents a sophisticated, unified architecture that provides:

- **Unified Theme Definition**: Single source of truth for all UI styling
- **Multi-Framework Support**: Consistent themes across CLI and TUI interfaces
- **Rich Color Management**: Advanced color operations and transformations
- **Performance Optimization**: Intelligent caching and lazy loading
- **Extensible Design**: Support for user themes and custom categories
- **Live Theme Switching**: Dynamic theme changes without restart
- **Comprehensive Integration**: Deep integration with all UI components

This architecture ensures that users get a consistent, beautiful interface across all application components while maintaining the flexibility to customize themes and optimize performance based on usage patterns. The unified approach eliminates theme inconsistencies and provides a seamless user experience throughout the application.
