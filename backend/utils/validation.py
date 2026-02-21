"""
Validation utilities for ZeroTrace
"""

import os

class Validator:
    """Simple validation class for paths and wiping methods"""

    @staticmethod
    def validate_path(path: str) -> bool:
        """Check if a path exists and is accessible"""
        if not os.path.exists(path):
            print(f"Validation error: Path does not exist: {path}")
            return False
        return True

    @staticmethod
    def validate_wipe_method(method: str) -> bool:
        """Ensure method is 'clear' or 'purge'"""
        if method not in ['clear', 'purge']:
            print(f"Validation error: Invalid wipe method: {method}")
            return False
        return True

