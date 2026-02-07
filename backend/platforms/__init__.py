"""
Platform Package
Provides OS-specific implementations for file operations
"""

import platform
from typing import Any


def get_platform_handler() -> Any:
    """
    Get the appropriate platform handler for current OS
    
    Returns:
        Platform-specific handler instance
    """
    os_type = platform.system()
    
    if os_type == 'Linux':
        from .platform_linux import LinuxPlatform
        return LinuxPlatform()
    elif os_type == 'Windows':
        from .platform_windows import WindowsPlatform
        return WindowsPlatform()
    elif os_type == 'Darwin':  # macOS
        from .platform_macos import MacOSPlatform
        return MacOSPlatform()
    else:
        raise OSError(f"Unsupported operating system: {os_type}")


__all__ = ['get_platform_handler']