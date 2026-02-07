"""
Validation Module
Validates user input and system state to ensure safe operations
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from utils.logging import Logger


class Validator:
    """Validates inputs and system state"""
    
    def __init__(self):
        """Initialize validator"""
        self.logger = Logger()
    
    def validate_path(self, path: str) -> Dict[str, any]:
        """
        Validate that a path exists and is accessible
        
        Args:
            path: Path to validate
        
        Returns:
            Validation result dictionary
        """
        result = {
            'valid': False,
            'exists': False,
            'accessible': False,
            'type': None,
            'errors': []
        }
        
        try:
            # Check for null bytes or control characters
            if '\x00' in path or any(ord(c) < 32 for c in path if c not in '\t\n\r'):
                result['errors'].append('Path contains invalid characters')
                return result
            
            path_obj = Path(path)
            
            # Check if exists
            if not path_obj.exists():
                result['errors'].append('Path does not exist')
                return result
            
            result['exists'] = True
            
            # Determine type
            if path_obj.is_file():
                result['type'] = 'file'
            elif path_obj.is_dir():
                result['type'] = 'directory'
            elif path_obj.is_symlink():
                result['type'] = 'symlink'
                result['errors'].append('Symbolic links are not supported')
                return result
            else:
                result['type'] = 'unknown'
                result['errors'].append('Unknown path type')
                return result
            
            # Check accessibility
            if not os.access(str(path_obj), os.R_OK):
                result['errors'].append('Path is not readable')
                return result
            
            result['accessible'] = True
            result['valid'] = True
            
        except Exception as e:
            result['errors'].append(f'Validation error: {str(e)}')
        
        return result
    
    def validate_permissions(self, path: str) -> Dict[str, any]:
        """
        Validate that we have permission to delete a file
        
        Args:
            path: Path to check
        
        Returns:
            Permission validation result
        """
        result = {
            'can_delete': False,
            'readable': False,
            'writable': False,
            'parent_writable': False,
            'errors': []
        }
        
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                result['errors'].append('Path does not exist')
                return result
            
            # Check file permissions
            result['readable'] = os.access(str(path_obj), os.R_OK)
            result['writable'] = os.access(str(path_obj), os.W_OK)
            
            # Check parent directory permissions (needed for deletion)
            parent = path_obj.parent
            result['parent_writable'] = os.access(str(parent), os.W_OK)
            
            # Can delete if both file is writable and parent directory is writable
            if result['writable'] and result['parent_writable']:
                result['can_delete'] = True
            else:
                if not result['writable']:
                    result['errors'].append('File is not writable')
                if not result['parent_writable']:
                    result['errors'].append('Parent directory is not writable')
            
        except Exception as e:
            result['errors'].append(f'Permission check error: {str(e)}')
        
        return result
    
    def validate_selection(self, file_list: List[str], 
                          platform_handler=None) -> Dict[str, any]:
        """
        Validate a list of files for deletion
        
        Args:
            file_list: List of file paths
            platform_handler: Optional platform handler for system file checking
        
        Returns:
            Validation result with warnings and errors
        """
        result = {
            'valid': True,
            'total_files': len(file_list),
            'valid_files': [],
            'invalid_files': [],
            'system_files': [],
            'warnings': [],
            'errors': []
        }
        
        if not file_list:
            result['valid'] = False
            result['errors'].append('No files selected')
            return result
        
        for file_path in file_list:
            # Validate path
            path_result = self.validate_path(file_path)
            
            if not path_result['valid']:
                result['invalid_files'].append({
                    'path': file_path,
                    'reasons': path_result['errors']
                })
                continue
            
            # Check if it's a system file
            if platform_handler and platform_handler.is_system_file(file_path.lower()):
                result['system_files'].append(file_path)
                result['warnings'].append(
                    f'WARNING: {file_path} appears to be a system file'
                )
                continue
            
            # Check permissions
            perm_result = self.validate_permissions(file_path)
            
            if not perm_result['can_delete']:
                result['invalid_files'].append({
                    'path': file_path,
                    'reasons': perm_result['errors']
                })
                continue
            
            # File is valid for deletion
            result['valid_files'].append(file_path)
        
        # Update validity
        if result['system_files']:
            result['valid'] = False
            result['errors'].append(
                f'{len(result["system_files"])} system file(s) detected - '
                'deletion not allowed'
            )
        
        if len(result['valid_files']) == 0:
            result['valid'] = False
            result['errors'].append('No valid files to delete')
        
        self.logger.log_info(
            f"Validation: {len(result['valid_files'])}/{len(file_list)} files valid"
        )
        
        return result
    
    def validate_wipe_method(self, method: str) -> bool:
        """
        Validate wiping method
        
        Args:
            method: Method name ('clear' or 'purge')
        
        Returns:
            True if valid
        """
        valid_methods = ['clear', 'purge']
        
        if method.lower() not in valid_methods:
            self.logger.log_error(f'Invalid wipe method: {method}')
            return False
        
        return True
    
    def check_disk_space(self, path: str, required_space: int = 0) -> Dict[str, any]:
        """
        Check if there's enough disk space
        
        Args:
            path: Path to check
            required_space: Required space in bytes
        
        Returns:
            Disk space check result
        """
        import psutil
        from utils.helpers import format_file_size
        
        result = {
            'sufficient': False,
            'available': 0,
            'required': required_space,
            'errors': []
        }
        
        try:
            usage = psutil.disk_usage(path)
            result['available'] = usage.free
            
            if usage.free >= required_space:
                result['sufficient'] = True
            else:
                result['errors'].append(
                    f'Insufficient disk space: '
                    f'{format_file_size(usage.free)} available, '
                    f'{format_file_size(required_space)} required'
                )
            
        except Exception as e:
            result['errors'].append(f'Disk space check error: {str(e)}')
        
        return result
    
    def validate_file_list_safety(self, file_list: List[str]) -> Dict[str, any]:
        """
        Perform comprehensive safety checks on file list
        
        Args:
            file_list: List of files to check
        
        Returns:
            Safety validation result
        """
        result = {
            'safe': True,
            'warnings': [],
            'critical_warnings': [],
            'statistics': {
                'total_files': len(file_list),
                'total_size': 0,
                'large_files': 0,  # > 1 GB
                'hidden_files': 0,
                'executable_files': 0
            }
        }
        
        from utils.helpers import is_hidden_file, format_file_size
        
        LARGE_FILE_THRESHOLD = 1024 * 1024 * 1024  # 1 GB
        
        for file_path in file_list:
            try:
                path_obj = Path(file_path)
                
                if not path_obj.exists():
                    continue
                
                # Get file size
                size = path_obj.stat().st_size
                result['statistics']['total_size'] += size
                
                # Check for large files
                if size > LARGE_FILE_THRESHOLD:
                    result['statistics']['large_files'] += 1
                    result['warnings'].append(
                        f'Large file detected: {file_path} ({format_file_size(size)})'
                    )
                
                # Check for hidden files
                if is_hidden_file(file_path):
                    result['statistics']['hidden_files'] += 1
                
                # Check for executables
                if path_obj.suffix.lower() in ['.exe', '.dll', '.so', '.dylib', '.app']:
                    result['statistics']['executable_files'] += 1
                    result['warnings'].append(
                        f'Executable file detected: {file_path}'
                    )
                
            except Exception as e:
                self.logger.log_warning(f'Error checking {file_path}: {e}')
        
        # Add summary warnings
        if result['statistics']['large_files'] > 0:
            result['warnings'].append(
                f'{result["statistics"]["large_files"]} large file(s) - '
                'deletion may take significant time'
            )
        
        total_size = result['statistics']['total_size']
        if total_size > 10 * 1024 * 1024 * 1024:  # > 10 GB
            result['critical_warnings'].append(
                f'WARNING: Deleting {format_file_size(total_size)} of data'
            )
        
        return result
    
    def require_user_confirmation(self, file_list: List[str]) -> bool:
        """
        Determine if user confirmation is required
        
        Args:
            file_list: List of files
        
        Returns:
            True if confirmation required
        """
        # Always require confirmation for:
        # - More than 10 files
        # - Any system files
        # - Total size > 1 GB
        
        if len(file_list) > 10:
            return True
        
        total_size = 0
        for file_path in file_list:
            try:
                total_size += Path(file_path).stat().st_size
            except Exception:
                continue
        
        if total_size > 1024 * 1024 * 1024:  # > 1 GB
            return True
        
        return False