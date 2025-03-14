"""
Parsing utilities for consistent handling of user inputs.
"""


def split_comma_separated(input_string: str) -> list:
    """
    Split a comma-separated string into a list of trimmed, non-empty items.

    Args:
        input_string: String possibly containing comma-separated values

    Returns:
        List of trimmed, non-empty strings
    """
    if not input_string:
        return []

    if "," not in input_string:
        return [input_string.strip()]

    return [item.strip() for item in input_string.split(",") if item.strip()]
