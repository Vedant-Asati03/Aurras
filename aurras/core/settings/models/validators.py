"""
Settings Validators

This module provides validation functions for settings values.
"""

def validate_volume(v):
    """
    Ensure volume is between 0 and 200.

    Args:
        v: The volume value to validate

    Returns:
        Validated volume as a string
    """
    try:
        vol = int(v)
        if vol < 0 or vol > 200:
            return "100"  # Default if out of range
        return str(vol)
    except (ValueError, TypeError):
        return "100"  # Default if conversion fails
