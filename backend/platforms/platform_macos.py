"""
macOS Platform Module
macOS-specific file and device operations
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import psutil


class MacOSPlatform:
    """macOS-specific platform operations"""
    
    def __init__(self):
        """Initialize macOS platform handler"""
        self.os_name = "macOS"
    
    def list_drives(self) -> List[Dict[str, any]]:
        """
        List all storage drives and volumes
        
        Returns:
            List of drive information dictionaries
        """
        drives = []
        
        try:
            partitions = psutil.disk_partitions(all=False)
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    drives.append({
                        'device': partition.device,
                        'mount_point': partition.mountpoint,
                        'fstype': partition.fstype,
                        'options': partition.opts,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                except PermissionError:
                    continue
            
        except Exception as e:
            print(f"Error listing drives: {e}")
        
        return drives
    
    def get_volumes(self) -> List[str]:
        """
        Get all mounted volumes
        
        Returns:
            List of volume paths
        """
        volumes = []
        
        try:
            volumes_path = Path('/Volumes')
            if volumes_path.exists():
                for volume in volumes_path.iterdir():
                    if volume.is_dir():
                        volumes.append(str(volume))
        except Exception as e:
            print(f"Error getting volumes: {e}")
        
        return volumes
    
    def secure_delete(self, path: str) -> bool:
        """
        Securely delete a file using macOS tools
        
        Args:
            path: File path to delete
        
        Returns:
            True if successful
        """
        try:
            # macOS has srm (secure rm) in some versions
            if self._command_exists('srm'):
                result = subprocess.run(
                    ['srm', '-s', path],  # -s: simple overwrite
                    capture_output=True
                )
                return result.returncode == 0
            else:
                # Fallback to regular deletion (after NIST overwrite)
                Path(path).unlink()
                return True
                
        except Exception as e:
            print(f"Error securely deleting {path}: {e}")
            return False
    
    def get_file_attributes(self, path: str) -> Optional[Dict[str, any]]:
        """
        Get macOS-specific file attributes
        
        Args:
            path: File path
        
        Returns:
            Dictionary with macOS-specific attributes
        """
        try:
            stat_info = os.stat(path)
            
            attributes = {
                'inode': stat_info.st_ino,
                'device': stat_info.st_dev,
                'nlink': stat_info.st_nlink,
                'uid': stat_info.st_uid,
                'gid': stat_info.st_gid,
                'mode': oct(stat_info.st_mode),
                'flags': stat_info.st_flags if hasattr(stat_info, 'st_flags') else 0
            }
            
            # Get extended attributes
            try:
                xattrs = os.listxattr(path)
                attributes['extended_attributes'] = list(xattrs)
            except (OSError, AttributeError):
                attributes['extended_attributes'] = []
            
            return attributes
            
        except Exception as e:
            print(f"Error getting file attributes: {e}")
            return None
    
    def handle_apfs(self, path: str) -> bool:
        """
        Handle APFS (Apple File System) specific operations
        
        Args:
            path: File path
        
        Returns:
            True if operations successful
        """
        try:
            # APFS-specific handling could go here
            # For now, just verify the filesystem type
            return self.get_filesystem_type(path) in ['apfs', 'hfs', 'hfsx']
        except Exception:
            return False
    
    def get_file_permissions(self, path: str) -> Dict[str, bool]:
        """
        Get file permission flags
        
        Args:
            path: File path
        
        Returns:
            Dictionary with permission flags
        """
        try:
            return {
                'readable': os.access(path, os.R_OK),
                'writable': os.access(path, os.W_OK),
                'executable': os.access(path, os.X_OK)
            }
        except Exception:
            return {'readable': False, 'writable': False, 'executable': False}
    
    def is_system_file(self, path: str) -> bool:
        """
        Check if file is a critical macOS system file
        
        Args:
            path: File path (lowercase)
        
        Returns:
            True if system file
        """
        # Critical macOS system directories
        system_paths = [
            '/system/', '/private/', '/usr/bin/', '/usr/sbin/',
            '/usr/lib/', '/bin/', '/sbin/', '/boot/',
            '/library/extensions/', '/system/library/',
            '/private/var/db/', '/private/var/vm/'
        ]
        
        for sys_path in system_paths:
            if path.startswith(sys_path):
                return True
        
        return False
    
    def get_disk_info(self, device: str) -> Optional[Dict[str, any]]:
        """
        Get disk information using diskutil
        
        Args:
            device: Device path (e.g., /dev/disk1)
        
        Returns:
            Disk information dictionary
        """
        try:
            result = subprocess.run(
                ['diskutil', 'info', '-plist', device],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse plist output
                import plistlib
                disk_info = plistlib.loads(result.stdout.encode())
                return dict(disk_info)
            
        except Exception as e:
            print(f"Error getting disk info: {e}")
        
        return None
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            result = subprocess.run(
                ['which', command],
                capture_output=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_filesystem_type(self, path: str) -> Optional[str]:
        """
        Get filesystem type for a path
        
        Args:
            path: File or directory path
        
        Returns:
            Filesystem type (apfs, hfs, etc.)
        """
        try:
            partitions = psutil.disk_partitions()
            
            path_obj = Path(path).resolve()
            
            for partition in partitions:
                mount_point = Path(partition.mountpoint)
                try:
                    if path_obj.is_relative_to(mount_point):
                        return partition.fstype
                except (ValueError, AttributeError):
                    # Fallback for older Python versions
                    if str(path_obj).startswith(str(mount_point)):
                        return partition.fstype
            
        except Exception:
            pass
        
        return None
    
    def empty_trash(self) -> bool:
        """
        Empty the macOS Trash
        
        Returns:
            True if successful
        """
        try:
            trash_path = Path.home() / '.Trash'
            
            if trash_path.exists():
                for item in trash_path.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            import shutil
                            shutil.rmtree(item)
                    except Exception as e:
                        print(f"Error deleting {item}: {e}")
                
                return True
            
        except Exception as e:
            print(f"Error emptying trash: {e}")
        
        return False
    
    def secure_empty_trash(self) -> bool:
        """
        Securely empty the macOS Trash using secure deletion
        
        Returns:
            True if successful
        """
        try:
            # This would iterate through trash and use secure deletion
            # Placeholder for actual implementation
            return self.empty_trash()
        except Exception as e:
            print(f"Error securely emptying trash: {e}")
            return False
    
    def get_spotlight_metadata(self, path: str) -> Optional[Dict[str, any]]:
        """
        Get Spotlight metadata for a file
        
        Args:
            path: File path
        
        Returns:
            Metadata dictionary
        """
        try:
            result = subprocess.run(
                ['mdls', path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse mdls output (simple key-value parsing)
                metadata = {}
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        metadata[key.strip()] = value.strip()
                return metadata
            
        except Exception as e:
            print(f"Error getting Spotlight metadata: {e}")
        
        return None