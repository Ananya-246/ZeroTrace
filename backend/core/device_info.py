"""
Device Information Module
Provides detailed information about files, folders, and storage devices
"""

import os
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import psutil
from utils.logging import Logger
from utils.helpers import format_file_size, get_file_category


class DeviceInfo:
    """Provides detailed device and file information"""
    
    def __init__(self, platform_handler):
        """
        Initialize device info
        
        Args:
            platform_handler: Platform-specific handler
        """
        self.platform_handler = platform_handler
        self.logger = Logger()
        mimetypes.init()
    
    def get_file_size(self, path: str) -> int:
        """
        Get file size in bytes
        
        Args:
            path: File path
        
        Returns:
            File size in bytes, 0 if error
        """
        try:
            return Path(path).stat().st_size
        except (OSError, FileNotFoundError):
            return 0
    
    def get_file_type(self, path: str) -> str:
        """
        Get file type/category
        
        Args:
            path: File path
        
        Returns:
            File type category (document, image, video, etc.)
        """
        try:
            file_path = Path(path)
            extension = file_path.suffix.lower()
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # Categorize
            return get_file_category(extension, mime_type)
            
        except Exception as e:
            self.logger.log_warning(f"Could not determine file type for {path}: {e}")
            return 'unknown'
    
    def get_file_permissions(self, path: str) -> Dict[str, bool]:
        """
        Get file permissions
        
        Args:
            path: File path
        
        Returns:
            Dictionary with permission flags
        """
        try:
            file_path = Path(path)
            
            permissions = {
                'readable': os.access(str(file_path), os.R_OK),
                'writable': os.access(str(file_path), os.W_OK),
                'executable': os.access(str(file_path), os.X_OK),
                'deletable': self._is_deletable(file_path)
            }
            
            return permissions
            
        except Exception as e:
            self.logger.log_warning(f"Could not get permissions for {path}: {e}")
            return {
                'readable': False,
                'writable': False,
                'executable': False,
                'deletable': False
            }
    
    def _is_deletable(self, file_path: Path) -> bool:
        """Check if file can be deleted"""
        try:
            # Check if parent directory is writable
            parent = file_path.parent
            if not os.access(str(parent), os.W_OK):
                return False
            
            # Check if file itself is writable (needed for secure deletion)
            if file_path.exists() and not os.access(str(file_path), os.W_OK):
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_disk_usage(self, path: str = None) -> Dict[str, any]:
        """
        Get disk usage information
        
        Args:
            path: Path to check (None = all disks)
        
        Returns:
            Dictionary with disk usage information
        """
        try:
            if path:
                usage = psutil.disk_usage(path)
                return {
                    'path': path,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent,
                    'total_formatted': format_file_size(usage.total),
                    'used_formatted': format_file_size(usage.used),
                    'free_formatted': format_file_size(usage.free)
                }
            else:
                # All partitions
                partitions = psutil.disk_partitions()
                disk_info = []
                
                for partition in partitions:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_info.append({
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percent': usage.percent,
                            'total_formatted': format_file_size(usage.total),
                            'used_formatted': format_file_size(usage.used),
                            'free_formatted': format_file_size(usage.free)
                        })
                    except PermissionError:
                        continue
                
                return {'disks': disk_info}
                
        except Exception as e:
            self.logger.log_error(f"Error getting disk usage: {e}")
            return {}
    
    def get_detailed_file_info(self, path: str) -> Dict[str, any]:
        """
        Get comprehensive file information
        
        Args:
            path: File path
        
        Returns:
            Dictionary with detailed file information
        """
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return {'error': 'File does not exist'}
            
            stat_info = file_path.stat()
            
            info = {
                'name': file_path.name,
                'path': str(file_path.absolute()),
                'size': stat_info.st_size,
                'size_formatted': format_file_size(stat_info.st_size),
                'extension': file_path.suffix,
                'type': self.get_file_type(path),
                'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir(),
                'is_symlink': file_path.is_symlink(),
                'permissions': self.get_file_permissions(path)
            }
            
            # Add platform-specific info
            platform_info = self.platform_handler.get_file_attributes(path)
            if platform_info:
                info['platform_specific'] = platform_info
            
            return info
            
        except Exception as e:
            self.logger.log_error(f"Error getting file info for {path}: {e}")
            return {'error': str(e)}
    
    def get_folder_info(self, path: str) -> Dict[str, any]:
        """
        Get information about a folder
        
        Args:
            path: Folder path
        
        Returns:
            Dictionary with folder information
        """
        try:
            folder_path = Path(path)
            
            if not folder_path.is_dir():
                return {'error': 'Not a directory'}
            
            # Count files and subdirectories
            file_count = 0
            dir_count = 0
            total_size = 0
            
            for item in folder_path.iterdir():
                try:
                    if item.is_file():
                        file_count += 1
                        total_size += item.stat().st_size
                    elif item.is_dir():
                        dir_count += 1
                except (PermissionError, OSError):
                    continue
            
            return {
                'name': folder_path.name,
                'path': str(folder_path.absolute()),
                'file_count': file_count,
                'dir_count': dir_count,
                'total_size': total_size,
                'total_size_formatted': format_file_size(total_size),
                'is_dir': True
            }
            
        except Exception as e:
            self.logger.log_error(f"Error getting folder info for {path}: {e}")
            return {'error': str(e)}
    
    def calculate_space_to_free(self, file_list: List[str]) -> Dict[str, any]:
        """
        Calculate how much space will be freed
        
        Args:
            file_list: List of file paths
        
        Returns:
            Dictionary with space calculation
        """
        total_size = 0
        file_count = 0
        error_count = 0
        
        for file_path in file_list:
            try:
                size = self.get_file_size(file_path)
                total_size += size
                file_count += 1
            except Exception:
                error_count += 1
        
        return {
            'total_size': total_size,
            'total_size_formatted': format_file_size(total_size),
            'file_count': file_count,
            'error_count': error_count
        }
    
    def is_system_file(self, path: str) -> bool:
        """
        Check if file is a critical system file
        
        Args:
            path: File path
        
        Returns:
            True if system file, False otherwise
        """
        try:
            file_path = Path(path).absolute()
            path_str = str(file_path).lower()
            
            # Platform-specific system file detection
            return self.platform_handler.is_system_file(path_str)
            
        except Exception:
            return False
    
    def get_file_hash(self, path: str, algorithm: str = 'sha256') -> Optional[str]:
        """
        Calculate file hash (for verification)
        
        Args:
            path: File path
            algorithm: Hash algorithm (md5, sha1, sha256)
        
        Returns:
            Hex digest of hash or None if error
        """
        import hashlib
        
        try:
            if algorithm == 'md5':
                hasher = hashlib.md5()
            elif algorithm == 'sha1':
                hasher = hashlib.sha1()
            else:
                hasher = hashlib.sha256()
            
            with open(path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except Exception as e:
            self.logger.log_warning(f"Could not hash file {path}: {e}")
            return None
    
    def verify_file_integrity(self, path: str) -> bool:
        """
        Verify file can be read and is not corrupted
        
        Args:
            path: File path
        
        Returns:
            True if file is accessible and readable
        """
        try:
            file_path = Path(path)
            
            # Check if file exists
            if not file_path.exists():
                return False
            
            # Try to read first and last bytes
            with open(file_path, 'rb') as f:
                f.read(1)  # First byte
                if file_path.stat().st_size > 1:
                    f.seek(-1, 2)  # Last byte
                    f.read(1)
            
            return True
            
        except Exception as e:
            self.logger.log_warning(f"File integrity check failed for {path}: {e}")
            return False