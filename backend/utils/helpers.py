"""
Helper Functions Module
General utility functions used throughout the application
"""

import re
from pathlib import Path
from typing import Optional


def format_file_size(bytes_size: int) -> str:
    """
    Convert bytes to human-readable format
    
    Args:
        bytes_size: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    if bytes_size < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(bytes_size)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def format_time(seconds: float) -> str:
    """
    Convert seconds to human-readable time format
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted string (e.g., "1h 30m 45s")
    """
    if seconds < 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return ' '.join(parts)


def sanitize_path(path: str) -> str:
    """
    Remove dangerous characters from file paths
    
    Args:
        path: File path to sanitize
    
    Returns:
        Sanitized path
    """
    # Remove null bytes
    path = path.replace('\x00', '')
    
    # Remove control characters
    path = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', path)
    
    # Normalize path separators
    path = path.replace('\\', '/')
    
    # Remove multiple consecutive slashes
    path = re.sub(r'/+', '/', path)
    
    return path


def calculate_deletion_time(file_size: int, method: str = 'clear') -> float:
    """
    Estimate how long deletion will take
    
    Args:
        file_size: Size of file in bytes
        method: Wiping method ('clear' or 'purge')
    
    Returns:
        Estimated time in seconds
    """
    # Approximate write speed: 100 MB/s (conservative)
    WRITE_SPEED = 100 * 1024 * 1024
    
    if method == 'clear':
        passes = 1
    else:  # purge
        passes = 7
    
    return (file_size * passes) / WRITE_SPEED


def get_file_category(extension: str, mime_type: Optional[str] = None) -> str:
    """
    Categorize file by extension and MIME type
    
    Args:
        extension: File extension (e.g., '.jpg')
        mime_type: MIME type (e.g., 'image/jpeg')
    
    Returns:
        Category name
    """
    extension = extension.lower()
    
    # Image files
    if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico']:
        return 'image'
    if mime_type and mime_type.startswith('image/'):
        return 'image'
    
    # Video files
    if extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
        return 'video'
    if mime_type and mime_type.startswith('video/'):
        return 'video'
    
    # Audio files
    if extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a']:
        return 'audio'
    if mime_type and mime_type.startswith('audio/'):
        return 'audio'
    
    # Document files
    if extension in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']:
        return 'document'
    if mime_type and 'document' in mime_type:
        return 'document'
    
    # Spreadsheet files
    if extension in ['.xls', '.xlsx', '.csv', '.ods']:
        return 'spreadsheet'
    if mime_type and 'spreadsheet' in mime_type:
        return 'spreadsheet'
    
    # Presentation files
    if extension in ['.ppt', '.pptx', '.odp']:
        return 'presentation'
    if mime_type and 'presentation' in mime_type:
        return 'presentation'
    
    # Archive files
    if extension in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz']:
        return 'archive'
    if mime_type and ('zip' in mime_type or 'compressed' in mime_type):
        return 'archive'
    
    # Code files
    if extension in ['.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs']:
        return 'code'
    if mime_type and 'text/' in mime_type:
        # Check if it's source code
        if extension in ['.html', '.css', '.xml', '.json', '.yaml', '.yml']:
            return 'code'
    
    # Executable files
    if extension in ['.exe', '.dll', '.so', '.dylib', '.app']:
        return 'executable'
    if mime_type and 'executable' in mime_type:
        return 'executable'
    
    # Default
    return 'other'


def validate_path_string(path: str) -> bool:
    """
    Validate that a path string is safe
    
    Args:
        path: Path to validate
    
    Returns:
        True if path is valid
    """
    if not path:
        return False
    
    # Check for null bytes
    if '\x00' in path:
        return False
    
    # Check for extremely long paths
    if len(path) > 4096:
        return False
    
    return True


def human_readable_to_bytes(size_str: str) -> Optional[int]:
    """
    Convert human-readable size to bytes
    
    Args:
        size_str: Size string (e.g., "1.5 GB")
    
    Returns:
        Size in bytes or None if invalid
    """
    size_str = size_str.strip().upper()
    
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
        'PB': 1024 ** 5
    }
    
    # Parse the string
    match = re.match(r'^([\d.]+)\s*([A-Z]+)$', size_str)
    if not match:
        return None
    
    value = float(match.group(1))
    unit = match.group(2)
    
    if unit not in units:
        return None
    
    return int(value * units[unit])


def get_safe_filename(filename: str) -> str:
    """
    Convert a string to a safe filename
    
    Args:
        filename: Original filename
    
    Returns:
        Safe filename
    """
    # Remove or replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    safe = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe)
    
    # Remove leading/trailing spaces and dots
    safe = safe.strip('. ')
    
    # Ensure it's not empty
    if not safe:
        safe = 'unnamed'
    
    # Limit length
    if len(safe) > 255:
        safe = safe[:255]
    
    return safe


def chunks(lst: list, n: int):
    """
    Yield successive n-sized chunks from list
    
    Args:
        lst: List to chunk
        n: Chunk size
    
    Yields:
        Chunks of the list
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def is_hidden_file(path: str) -> bool:
    """
    Check if a file is hidden
    
    Args:
        path: File path
    
    Returns:
        True if file is hidden
    """
    path_obj = Path(path)
    
    # Unix/Linux/macOS: files starting with dot
    if path_obj.name.startswith('.'):
        return True
    
    # Windows: check file attributes (if available)
    try:
        import platform
        if platform.system() == 'Windows':
            import win32api
            import win32con
            attrs = win32api.GetFileAttributes(path)
            return bool(attrs & win32con.FILE_ATTRIBUTE_HIDDEN)
    except (ImportError, Exception):
        pass
    
    return False