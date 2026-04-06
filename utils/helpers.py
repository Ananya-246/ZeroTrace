"""
Helper functions for ZeroTrace
"""

import datetime


def format_size(size_bytes: int) -> str:
    """
    Convert bytes to human-readable format.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.2f} PB"


def current_timestamp() -> str:
    """
    Return current UTC timestamp string.
    """
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
