# Aurras Theme System: Complete Guide

Welcome to the Aurras theme system! This guide will take you from basic theme usage to advanced theme development and system architecture. Whether you're a user wanting to customize themes or a contributor wanting to understand and extend the system, this document has you covered.

## Table of Contents

1. [Quick Start: Using Themes](#quick-start-using-themes)
2. [Understanding the Theme System](#understanding-the-theme-system)
3. [For Contributors: Code Tour](#for-contributors-code-tour)
4. [Creating Custom Themes](#creating-custom-themes)
5. [Advanced Integration](#advanced-integration)
6. [Reference](#reference)

---

## Quick Start: Using Themes

### Basic Theme Commands

```bash
# List all available themes
aurras theme

# Set a theme
aurras theme galaxy
aurras theme neon
aurras theme ocean
```

### Available Built-in Themes

Aurras includes 10 carefully crafted themes:

| Theme | Category | Description |
|-------|----------|-------------|
| **Galaxy** | Dark | Deep space-inspired with rich purples and blues |
| **Neon** | Vibrant | Bright digital visualization style |
| **Cyberpunk** | Vibrant | Futuristic cyberpunk aesthetic |
| **Ocean** | Natural | Calming blue oceanic palette |
| **Forest** | Natural | Earthy green natural environment |
| **Sunset** | Natural | Warm orange and pink sunset tones |
| **Vintage** | Light | Warm retro vinyl player feel |
| **Minimal** | Minimal | Clean distraction-free interface |
| **Nightclub** | Vibrant | Bold party atmosphere colors |
| **Monochrome** | Minimal | Classic black and white styling |

---

## Understanding the Theme System

### High-Level Architecture

```bash
User Commands → Theme Manager → Adapters → UI Frameworks
                     ↓              ↓
                Theme Storage   Rich/Textual
                                 Styling
```

The Aurras theme system is built on these core principles:

1. **Single Source of Truth**: One theme definition works across CLI and TUI
2. **Adapter Pattern**: Converts themes for different UI frameworks (Rich/Textual)
3. **Performance First**: Smart caching and lazy loading
4. **User Extensible**: Easy custom theme creation

### Key Components Overview

```bash
aurras/themes/
├── definitions.py     # ThemeDefinition and ThemeCategory classes
├── colors.py         # ThemeColor class with transformations
├── manager.py        # Central theme management API
├── themes.py         # All built-in theme definitions
├── utils.py          # Helper functions and caching
└── adapters/
    │
    to Rich format
    ├── rich_adapter.py     # Converts themes
    to Textual format
    └── textual_adapter.py  # Converts themes 
```

---

## For Contributors: Code Tour

Let's walk through the theme system step by step, perfect for new contributors!

### Step 1: Understanding Theme Data Structure

**File**: `aurras/themes/definitions.py`

The heart of the system is the `ThemeDefinition` class:

```python
@dataclass
class ThemeDefinition:
    # Basic metadata
    name: str                    # Unique identifier (e.g., "GALAXY")
    display_name: str           # User-friendly name (e.g., "Galaxy")
    description: str            # Brief description
    category: ThemeCategory     # DARK, LIGHT, VIBRANT, etc.
    dark_mode: bool            # True for dark themes
    
    # Core colors - the essential ones
    primary: Optional[ThemeColor]      # Main brand color
    secondary: Optional[ThemeColor]    # Secondary emphasis
    accent: Optional[ThemeColor]       # Highlights and focus
    
    # UI background colors
    background: Optional[ThemeColor]   # Main background
    surface: Optional[ThemeColor]      # Cards, panels
    panel: Optional[ThemeColor]        # Specific panel backgrounds
    
    # Status colors - for user feedback
    warning: Optional[ThemeColor]      # Warning messages
    error: Optional[ThemeColor]        # Error messages  
    success: Optional[ThemeColor]      # Success messages
    info: Optional[ThemeColor]         # Info messages
    
    # Text colors
    text: Optional[ThemeColor]         # Main text
    text_muted: Optional[ThemeColor]   # Secondary text
    border: Optional[ThemeColor]       # Borders and dividers
    
    # Gradients - for enhanced visuals
    title_gradient: Optional[List[str]]     # Song titles
    artist_gradient: Optional[List[str]]    # Artist names
    status_gradient: Optional[List[str]] = None     # System info
    progress_gradient: Optional[List[str]] = None    # Progress bar
    feedback_gradient: Optional[List[str]] = None    # Feedback
    history_gradient: Optional[List[str]] = None     # History song names

    # Special fields
    dim: str = "#333333"
```

**Why this design?**

- Optional fields allow themes to define only what they need
- Consistent structure across all themes
- Type safety with dataclasses
- Easy validation and defaults

### Step 2: Color Management

**File**: `aurras/themes/colors.py`

The `ThemeColor` class handles all color operations:

```python
@dataclass(frozen=True)
class ThemeColor:
    hex: str                              # "#FF5733"
    gradient: Optional[List[str]] = None  # ["#FF5733", "#FF6644"]
    
    # Color transformations
    def darken(self, amount: float) -> str:
        """Make color darker by specified amount (0.0-1.0)"""
        
    def lighten(self, amount: float) -> str:
        """Make color lighter by specified amount (0.0-1.0)"""
        
    def with_alpha(self, alpha: int) -> str:
        """Add transparency (0-100)"""
        
    def generate_gradient(self, steps: int) -> List[str]:
        """Generate a gradient with specified steps"""
```

**Example usage:**

```python
primary = ThemeColor("#FF5733")
darker = primary.darken(0.2)           # "#CC451F"
lighter = primary.lighten(0.1)         # "#FF6B4D"
transparent = primary.with_alpha(50)   # "#FF5733 50%"
```

### Step 3: Theme Management

**File**: `aurras/themes/manager.py`

This is the central API that everyone uses:

```python
# Core functions
def get_theme(theme_name: Optional[str] = None) -> ThemeDefinition
def get_available_themes() -> List[str]
def set_current_theme(theme_name: str) -> bool
def get_current_theme() -> str
def get_themes_by_category(category: Union[str, ThemeCategory]) -> Dict[str, ThemeDefinition]
```

**How it works:**

1. Maintains a global `_current_theme` variable
2. Loads themes on-demand from `AVAILABLE_THEMES`
3. Handles case-insensitive theme lookups
4. Provides category filtering

### Step 4: Built-in Themes

**File**: `aurras/themes/themes.py`

This file defines all the built-in themes. Here's how a theme is structured:

```python
GALAXY: Final[ThemeDefinition] = ThemeDefinition(
    name="GALAXY",
    display_name="Galaxy",
    description="Deep space-inspired theme with rich purples and blues",
    category=ThemeCategory.DARK,
    dark_mode=True,
    
    # Core colors
    primary=ThemeColor("#BD93F9"),      # Vibrant purple
    secondary=ThemeColor("#8BE9FD"),    # Bright cyan
    accent=ThemeColor("#FF79C6"),       # Pink
    
    # UI colors
    background=ThemeColor("#282A36"),   # Dark background
    surface=ThemeColor("#383A59"),      # Slightly lighter
    panel=ThemeColor("#44475A"),        # Panel color
    
    # Status colors
    warning=ThemeColor("#FFB86C"),      # Soft orange
    error=ThemeColor("#FF5555"),        # Bright red
    success=ThemeColor("#50FA7B"),      # Bright green
    
    # Text colors
    text=ThemeColor("#F8F8F2"),         # Light text
    text_muted=ThemeColor("#BFBFBF"),   # Muted text
    border=ThemeColor("#6272A4"),       # Border color
    
    # Gradients for visual enhancement
    title_gradient=["#BD93F9", "#B899FA", "#B39FFB", "#AEA5FC"],
    progress_gradient=["#40FA70", "#45FA74", "#4AFA78", "#50FA7B"],
    # ... more gradients
)
```

**Key points:**

- Each theme is a `Final` constant for immutability
- Colors are carefully chosen for accessibility and aesthetics
- Gradients enhance visual appeal
- All themes follow the same structure

### Step 5: The Adapter System

This is where the magic happens! Adapters convert our unified theme format to framework-specific formats.

#### Rich Adapter (CLI)

**File**: `aurras/themes/adapters/rich_adapter.py`

```python
def theme_to_rich_theme(theme_def: ThemeDefinition) -> RichTheme:
    """Convert ThemeDefinition to Rich Theme"""
    
    # Define style mappings with fallbacks
    style_mapping = {
        "primary": (
            theme_def.primary.hex if theme_def.primary else None,
            [],  # No fallbacks for primary
            "#FFFFFF",  # Default fallback
        ),
        "success": (
            theme_def.success.hex if theme_def.success else None,
            [theme_def.accent.hex if theme_def.accent else None],  # Try accent
            "#00FF00",  # Default green
        ),
        # ... more mappings
    }
```

**Why fallbacks?** If a theme doesn't define a `success` color, it tries `accent`, then falls back to default green.

#### Textual Adapter (TUI)

**File**: `aurras/themes/adapters/textual_adapter.py`

Similar concept but converts to Textual's theme format for the TUI interface.

### Step 6: Console Integration

**File**: `aurras/utils/console/manager.py`

The `ThemedConsole` class extends Rich's Console with theme awareness:

```python
class ThemedConsole(Console):
    @property
    def primary(self):
        """Get primary color from current theme"""
        return self.theme_obj.primary.hex
    
    def print_error(self, message: str, **kwargs):
        """Print error with theme's error color"""
        self.print_styled(message, "error", **kwargs)
    
    def print_success(self, message: str, **kwargs):
        """Print success with theme's success color"""
        self.print_styled(message, "success", **kwargs)
```

**Global Console Instance:**

```python
# In aurras/utils/console/__init__.py
console = get_console()  # Global themed console
```

This means anywhere in the codebase, you can:

```python
from aurras.utils.console import console
console.print_success("Theme applied successfully!")
```

### Step 7: User Theme Loading

**File**: `aurras/themes/themes.py` (function `_load_user_themes`)

```python
def _load_user_themes() -> Dict[str, ThemeDefinition]:
    """Load user themes from ~/.aurras/config/themes.yaml"""
    
    # Read YAML file
    with open(USER_THEME_CONFIG_FILE, "r") as f:
        themes_data = yaml.safe_load(f)
    
    # Convert each theme to ThemeDefinition
    for theme_name, properties in themes_data.items():
        theme_obj = ThemeDefinition.from_dict(properties)
        user_themes[theme_obj.name] = theme_obj
```

**Integration:**

```python
# All themes (built-in + user) in one place
AVAILABLE_THEMES = {
    GALAXY.name: GALAXY,
    NEON.name: NEON,
    # ... all built-in themes
    **{theme.name: theme for theme in user_themes.values()},  # User themes
}
```

---

## Creating Custom Themes

### Step 1: Create the Theme File

Create `~/.aurras/config/themes.yaml`:

```yaml
DRACULA:
  name: "DRACULA"
  display_name: "Dracula"
  description: "The famous dark theme with purple, pink, and cyan colors"
  category: "CUSTOM"
  dark_mode: true

  # Core colors
  primary: "#BD93F9"      # Purple
  secondary: "#8BE9FD"    # Cyan
  accent: "#FF79C6"       # Pink

  # UI background colors
  background: "#282A36"   # Dark background
  surface: "#44475A"      # Lighter surface
  panel: "#6272A4"        # Panel color

  # Status colors
  warning: "#FFB86C"      # Orange
  error: "#FF5555"        # Red
  success: "#50FA7B"      # Green
  info: "#8BE9FD"         # Cyan

  # Text colors
  text: "#F8F8F2"         # Foreground
  text_muted: "#6272A4"   # Comment
  text_secondary: "#BFBFBF"

  # Interactive colors
  hover: "#6272A4"
  selected: "#44475A"
  focus: "#BD93F9"

  # Border colors
  border: "#6272A4"
  border_focus: "#BD93F9"

  # Progress colors
  progress_bar: "#BD93F9"
  progress_background: "#44475A"

  # Gradients for enhanced visuals
  title_gradient: ["#BD93F9", "#FF79C6", "#8BE9FD"]
  artist_gradient: ["#8BE9FD", "#50FA7B", "#FFB86C"]
  progress_gradient: ["#BD93F9", "#FF79C6", "#50FA7B"]
```

### Step 2: Test Your Theme

```bash
# Reload Aurras to pick up the new theme
aurras theme

# Your theme should appear in the list
aurras theme my_awesome_theme
```

### Step 3: Theme Design Tips

1. **Start with core colors**: `primary`, `secondary`, `accent` are most important
2. **Ensure contrast**: Text should be readable on backgrounds
3. **Use gradients sparingly**: They enhance but shouldn't overwhelm
4. **Test in both CLI and TUI**: Themes work across both interfaces
5. **Consider accessibility**: Avoid red-green combinations for colorblind users

### Advanced Theme Features

#### Color Transformations

```yaml
MY_THEME:
  # ... other properties
  
  # You can reference colors in gradients
  title_gradient: 
    - primary        # Reference to primary color
    - "#FF8FB3"      # Custom color
    - "primary-light" # Transformed color (if supported)
```

#### Category Organization

```yaml
MY_PROFESSIONAL_THEME:
  category: "MINIMAL"   # Groups with other minimal themes

MY_GAMING_THEME:
  category: "VIBRANT"   # Groups with other vibrant themes
```

---

## Advanced Integration

### Using Themes in Your Code

#### Basic Usage

```python
from aurras.utils.console import console

# The console is automatically themed
console.print("Hello World!", style="primary")
console.print_error("Something went wrong!")
console.print_success("Operation completed!")
```

#### Direct Theme Access

```python
from aurras.themes.manager import get_theme

# Get current theme
theme = get_theme()
print(f"Primary color: {theme.primary.hex}")
print(f"Theme name: {theme.display_name}")

# Get specific theme
galaxy_theme = get_theme("GALAXY")
darker_primary = galaxy_theme.primary.darken(0.2)
```

#### Theme-Aware Components

```python
from aurras.utils.console import console

# Create themed Rich components
table = console.create_table(title="My Data")
panel = console.create_panel("Content", title="Info")
```

#### Custom Rich Console (Advanced)

```python
from aurras.themes.adapters import theme_to_rich_theme
from aurras.themes.manager import get_theme
from rich.console import Console

# Create custom console with specific theme
theme = get_theme("CYBERPUNK")
rich_theme = theme_to_rich_theme(theme)
custom_console = Console(theme=rich_theme)

custom_console.print("Cyberpunk styled!", style="primary")
```

#### Textual TUI Integration

```python
from aurras.themes.adapters import theme_to_textual_theme
from aurras.themes.manager import get_theme
from textual.app import App

class MyApp(App):
    def __init__(self):
        super().__init__()
        
        # Apply theme to TUI
        theme = get_theme("NEON")
        textual_theme = theme_to_textual_theme(theme)
        self.theme = textual_theme.name
        self.register_theme(textual_theme)
```

### Performance Considerations

The theme system includes several performance optimizations:

1. **Caching**: Converted themes are cached to avoid recomputation
2. **Lazy Loading**: Themes load only when needed
3. **Immutable Objects**: Theme definitions are immutable for thread safety
4. **LRU Eviction**: Cache automatically manages memory usage

### Adding New Built-in Themes

To add a new built-in theme:

1. **Define the theme** in `aurras/themes/themes.py`:

```python
MY_NEW_THEME: Final[ThemeDefinition] = ThemeDefinition(
    name="MY_NEW_THEME",
    display_name="My New Theme",
    description="Description of the theme",
    category=ThemeCategory.DARK,  # Choose appropriate category
    # ... color definitions
)
```

2. **Add to available themes**:

```python
AVAILABLE_THEMES: Final[Dict[str, ThemeDefinition]] = {
    # ... existing themes
    MY_NEW_THEME.name: MY_NEW_THEME,
    # ... rest of themes
}
```

3. **Test thoroughly** in both CLI and TUI modes

### Extending Color Functionality

To add new color transformation methods:

1. **Add method to ThemeColor** in `aurras/themes/colors.py`:

```python
def saturate(self, amount: float) -> str:
    """Increase color saturation"""
    # Implementation here
```

2. **Update adapters** if needed to use new functionality

---

## Reference

### File Structure Complete

```
aurras/themes/
├── __init__.py                    # Package initialization
├── definitions.py                 # ThemeDefinition, ThemeCategory classes
├── colors.py                     # ThemeColor class with transformations
├── manager.py                    # Central theme management API
├── themes.py                     # Built-in theme definitions
├── utils.py                      # Helper functions, caching utilities
└── adapters/
    ├── __init__.py               # Adapter exports
    ├── rich_adapter.py           # Rich framework adapter
    └── textual_adapter.py        # Textual framework adapter

aurras/utils/console/
├── __init__.py                   # Console exports
├── manager.py                    # ThemedConsole class
├── formatting.py                 # Text formatting utilities
└── renderer.py                   # UI component renderers

aurras/tui/themes/
├── __init__.py                   # TUI theme exports
└── theme_manager.py              # TUI-specific theme management
```

### Core Classes Reference

#### ThemeDefinition

**Location**: `aurras/themes/definitions.py`

**Purpose**: Central data structure for theme definitions

**Key Attributes**:

- `name: str` - Unique identifier (uppercase)
- `display_name: str` - User-friendly name
- `description: str` - Brief description
- `category: ThemeCategory` - Theme category
- `dark_mode: bool` - Whether it's a dark theme
- Color attributes: `primary`, `secondary`, `accent`, `background`, etc.
- Gradient attributes: `title_gradient`, `progress_gradient`, etc.

#### ThemeColor

**Location**: `aurras/themes/colors.py`

**Purpose**: Color management with transformations

**Key Methods**:

- `darken(amount: float) -> str` - Make color darker
- `lighten(amount: float) -> str` - Make color lighter  
- `with_alpha(alpha: int) -> str` - Add transparency
- `generate_gradient(steps: int) -> List[str]` - Create gradient

#### ThemedConsole

**Location**: `aurras/utils/console/manager.py`

**Purpose**: Rich Console with automatic theme integration

**Key Methods**:

- `print_error(message)` - Print with error color
- `print_success(message)` - Print with success color
- `print_info(message)` - Print with info color
- `style_text(text, style_key)` - Apply theme styling
- Color properties: `primary`, `secondary`, `accent`, etc.

### API Reference

#### Theme Manager Functions

```python
# Get themes
get_theme(theme_name: Optional[str]) -> ThemeDefinition
get_available_themes() -> List[str]
get_current_theme() -> str
get_themes_by_category(category) -> Dict[str, ThemeDefinition]

# Set themes
set_current_theme(theme_name: str) -> bool
```

#### Adapter Functions

```python
# Rich adapter
theme_to_rich_theme(theme_def: ThemeDefinition) -> RichTheme

# Textual adapter  
theme_to_textual_theme(theme_def: ThemeDefinition) -> TextualTheme
```

### Theme Categories

- `ThemeCategory.DARK` - Dark themes
- `ThemeCategory.LIGHT` - Light themes  
- `ThemeCategory.VIBRANT` - High-contrast, colorful themes
- `ThemeCategory.MINIMAL` - Clean, simple themes
- `ThemeCategory.NATURAL` - Earth-inspired themes
- `ThemeCategory.FUTURISTIC` - Tech/sci-fi themes
- `ThemeCategory.RETRO` - Vintage-inspired themes
- `ThemeCategory.CUSTOM` - User-created themes

### Command Line Interface

```bash
# List all themes
aurras theme

# Set theme
aurras theme <theme_name>

# Examples
aurras theme galaxy
aurras theme neon
aurras theme my_custom_theme
```

---

## Troubleshooting

### Common Issues

1. **Theme not found**
   - Check spelling: theme names are case-insensitive
   - Verify theme exists: `aurras theme` to list all

2. **Custom theme not loading**
   - Check file location: `~/.aurras/config/themes.yaml`
   - Validate YAML syntax
   - Check required fields: `name`, `display_name`

3. **Colors not displaying correctly**
   - Verify terminal supports colors
   - Check color format: use `#RRGGBB` format
   - Test with built-in themes first

4. **Theme changes not persisting**
   - Theme changes save automatically to settings
   - Check file permissions on config directory

### Development Tips

1. **Testing themes**: Use both CLI and TUI modes
2. **Color accessibility**: Test with colorblind simulators
3. **Performance**: Profile theme switching in large applications
4. **Debugging**: Enable debug logging for theme operations

---

This comprehensive guide should help you understand, use, and extend the Aurras theme system. Whether you're customizing your experience or contributing to the project, the theme system is designed to be powerful yet approachable.

For questions or contributions, check out the [CONTRIBUTING.md](../CONTRIBUTING.md) guide!
