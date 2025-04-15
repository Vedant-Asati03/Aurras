"""
Settings Utilities

This module provides utility functions for the settings models.
"""

from typing import Dict, Any


def dict_to_kebab_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dictionary keys from snake_case to kebab-case.

    Args:
        data: Dictionary with snake_case keys

    Returns:
        Dictionary with kebab-case keys
    """
    result = {}
    for k, v in data.items():
        # Convert snake_case to kebab-case
        key = k.replace("_", "-")
        if isinstance(v, dict):
            result[key] = dict_to_kebab_case(v)
        else:
            result[key] = v
    return result


def dict_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dictionary keys from kebab-case to snake_case.

    Args:
        data: Dictionary with kebab-case keys

    Returns:
        Dictionary with snake_case keys
    """
    result = {}
    for k, v in data.items():
        # Convert kebab-case to snake_case
        key = k.replace("-", "_")
        if isinstance(v, dict):
            result[key] = dict_to_snake_case(v)
        else:
            result[key] = v
    return result
