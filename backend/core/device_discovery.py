"""
Device Discovery Module
Discovers all storage devices, partitions, and files on the system
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from utils.logging import Logger


class DeviceDiscovery:
    """Discovers and scans storage devices and file systems"""
    
    def __init__(self, platform_handler):
        """
        Initialize device discovery
        
        Args:
            platform_handler: Platform-specific handler (Linux/Windows/macOS)
        """
        self.platform_handler = platform_handler
        self.logger = Logger()
        self._file_cache = {}
    
    def get_all_drives(self) -> List[Dict[str, any]]:
        """
        Get all available drives/partitions
        
        Returns:
            List of drive information dictionaries
        """
        try:
            drives = self.platform_handler.list_drives()
            self.logger.log_info(f"Discovered {len(drives)} drive(s)")
            return drives
        except Exception as e:
            self.logger.log_error(f"Error discovering drives: {e}")
            return []
    
    def scan_directory(self, path: str, recursive: bool = True, 
                      max_depth: Optional[int] = None) -> List[Dict[str, any]]:
        """
        Scan a directory and return all files
        
        Args:
            path: Directory path to scan
            recursive: Whether to scan subdirectories
            max_depth: Maximum depth to scan (None = unlimited)
        
        Returns:
            List of file information dictionaries
        """
        file_list = []
        
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                self.logger.log_warning(f"Path does not exist: {path}")
                return []
            
            if not path_obj.is_dir():
                self.logger.log_warning(f"Path is not a directory: {path}")
                return []
            
            # Scan the directory
            if recursive:
                file_list = self._scan_recursive(path_obj, max_depth, 0)
            else:
                file_list = self._scan_single_level(path_obj)
            
            self.logger.log_info(f"Scanned {path}: found {len(file_list)} files")
            return file_list
            
        except PermissionError:
            self.logger.log_warning(f"Permission denied: {path}")
            return []
        except Exception as e:
            self.logger.log_error(f"Error scanning directory {path}: {e}")
            return []
    
    def _scan_single_level(self, path_obj: Path) -> List[Dict[str, any]]:
        """Scan a single directory level"""
        file_list = []
        
        try:
            for item in path_obj.iterdir():
                try:
                    if item.is_file():
                        file_info = self._get_file_info(item)
                        if file_info:
                            file_list.append(file_info)
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            pass
        
        return file_list
    
    def _scan_recursive(self, path_obj: Path, max_depth: Optional[int], 
                       current_depth: int) -> List[Dict[str, any]]:
        """Recursively scan directory tree"""
        file_list = []
        
        # Check depth limit
        if max_depth is not None and current_depth >= max_depth:
            return file_list
        
        try:
            for item in path_obj.iterdir():
                try:
                    if item.is_file():
                        file_info = self._get_file_info(item)
                        if file_info:
                            file_list.append(file_info)
                    elif item.is_dir() and not item.is_symlink():
                        # Recursively scan subdirectory
                        sub_files = self._scan_recursive(
                            item, max_depth, current_depth + 1
                        )
                        file_list.extend(sub_files)
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            pass
        
        return file_list
    
    def _get_file_info(self, file_path: Path) -> Optional[Dict[str, any]]:
        """
        Get basic file information
        
        Args:
            file_path: Path object to file
        
        Returns:
            Dictionary with file information or None if error
        """
        try:
            stat_info = file_path.stat()
            
            return {
                'name': file_path.name,
                'path': str(file_path.absolute()),
                'size': stat_info.st_size,
                'extension': file_path.suffix,
                'modified': stat_info.st_mtime,
                'is_file': True,
                'is_dir': False
            }
        except (PermissionError, OSError, FileNotFoundError):
            return None
    
    def get_file_tree(self, root_path: str = None) -> Dict[str, any]:
        """
        Create a complete file tree structure
        
        Args:
            root_path: Root path to start from (None = all drives)
        
        Returns:
            Hierarchical tree structure
        """
        tree = {
            'name': 'Root',
            'type': 'root',
            'children': []
        }
        
        try:
            if root_path:
                # Single path tree
                tree['children'].append(self._build_tree_node(Path(root_path)))
            else:
                # All drives tree
                drives = self.get_all_drives()
                for drive in drives:
                    drive_path = drive.get('mount_point') or drive.get('device')
                    if drive_path:
                        tree['children'].append(self._build_tree_node(Path(drive_path)))
            
            return tree
            
        except Exception as e:
            self.logger.log_error(f"Error building file tree: {e}")
            return tree
    
    def _build_tree_node(self, path: Path, max_depth: int = 3, 
                        current_depth: int = 0) -> Dict[str, any]:
        """
        Build a tree node for the file tree
        
        Args:
            path: Path to build node for
            max_depth: Maximum depth to traverse
            current_depth: Current depth in tree
        
        Returns:
            Tree node dictionary
        """
        node = {
            'name': path.name or str(path),
            'path': str(path.absolute()),
            'type': 'directory' if path.is_dir() else 'file',
            'children': []
        }
        
        # Add size for files
        if path.is_file():
            try:
                node['size'] = path.stat().st_size
            except (PermissionError, OSError):
                node['size'] = 0
            return node
        
        # Limit depth
        if current_depth >= max_depth:
            node['truncated'] = True
            return node
        
        # Add children for directories
        try:
            for item in path.iterdir():
                try:
                    child_node = self._build_tree_node(
                        item, max_depth, current_depth + 1
                    )
                    node['children'].append(child_node)
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass
        
        return node
    
    def search_files(self, pattern: str, root_path: str = None) -> List[Dict[str, any]]:
        """
        Search for files matching a pattern
        
        Args:
            pattern: Glob pattern (e.g., '*.txt', '**/*.jpg')
            root_path: Root path to search from
        
        Returns:
            List of matching files
        """
        matches = []
        
        try:
            if root_path:
                search_path = Path(root_path)
            else:
                # Search all drives
                drives = self.get_all_drives()
                for drive in drives:
                    drive_path = drive.get('mount_point') or drive.get('device')
                    if drive_path:
                        matches.extend(self._search_in_path(Path(drive_path), pattern))
                return matches
            
            matches = self._search_in_path(search_path, pattern)
            
        except Exception as e:
            self.logger.log_error(f"Error searching files: {e}")
        
        return matches
    
    def _search_in_path(self, path: Path, pattern: str) -> List[Dict[str, any]]:
        """Search for files in a specific path"""
        matches = []
        
        try:
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    file_info = self._get_file_info(file_path)
                    if file_info:
                        matches.append(file_info)
        except (PermissionError, OSError):
            pass
        
        return matches
    
    def get_total_size(self, file_list: List[Dict[str, any]]) -> int:
        """
        Calculate total size of files in list
        
        Args:
            file_list: List of file dictionaries
        
        Returns:
            Total size in bytes
        """
        return sum(f.get('size', 0) for f in file_list)
    
    def clear_cache(self):
        """Clear the internal file cache"""
        self._file_cache.clear()
        self.logger.log_info("File cache cleared")