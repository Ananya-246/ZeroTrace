"""
Linux Platform Module
Linux-specific file and device operations
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import psutil


class WindowsPlatform:
    """Linux-specific platform operations"""
    
    def __init__(self):
        """Initialize Linux platform handler"""
        self.os_name = "Linux"
    
    def list_drives(self) -> List[Dict[str, any]]:
        """
        List all storage drives and partitions
        
        Returns:
            List of drive information dictionaries
        """
        drives = []
        
        try:
            # Use psutil to get partition information
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
    
    def get_mount_points(self) -> List[str]:
        """
        Get all mount points
        
        Returns:
            List of mount point paths
        """
        try:
            partitions = psutil.disk_partitions(all=False)
            return [p.mountpoint for p in partitions]
        except Exception:
            return []
    
    def secure_delete(self, path: str) -> bool:
        """
        Securely delete a file using Linux tools
        
        Args:
            path: File path to delete
        
        Returns:
            True if successful
        """
        try:
            # Check if shred is available
            if self._command_exists('shred'):
                # Use shred for secure deletion
                # -v: verbose, -z: add final overwrite with zeros, -u: remove file
                result = subprocess.run(
                    ['shred', '-v', '-z', '-u', path],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            else:
                # Fallback to regular deletion if shred not available
                Path(path).unlink()
                return True
                
        except Exception as e:
            print(f"Error securely deleting {path}: {e}")
            return False
    
    def get_file_attributes(self, path: str) -> Optional[Dict[str, any]]:
        """
        Get Linux-specific file attributes
        
        Args:
            path: File path
        
        Returns:
            Dictionary with Linux-specific attributes
        """
        try:
            stat_info = os.stat(path)
            
            return {
                'inode': stat_info.st_ino,
                'device': stat_info.st_dev,
                'nlink': stat_info.st_nlink,
                'uid': stat_info.st_uid,
                'gid': stat_info.st_gid,
                'mode': oct(stat_info.st_mode),
                'permissions': self._format_permissions(stat_info.st_mode)
            }
        except Exception:
            return None
    
    def _format_permissions(self, mode: int) -> str:
        """Format file permissions in rwx format"""
        perms = []
        
        # Owner permissions
        perms.append('r' if mode & 0o400 else '-')
        perms.append('w' if mode & 0o200 else '-')
        perms.append('x' if mode & 0o100 else '-')
        
        # Group permissions
        perms.append('r' if mode & 0o040 else '-')
        perms.append('w' if mode & 0o020 else '-')
        perms.append('x' if mode & 0o010 else '-')
        
        # Other permissions
        perms.append('r' if mode & 0o004 else '-')
        perms.append('w' if mode & 0o002 else '-')
        perms.append('x' if mode & 0o001 else '-')
        
        return ''.join(perms)
    
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
        Check if file is a critical system file
        
        Args:
            path: File path (lowercase)
        
        Returns:
            True if system file
        """
        # Critical Linux system directories
        system_paths = [
            '/bin/', '/sbin/', '/boot/', '/dev/', '/proc/', '/sys/',
            '/lib/', '/lib64/', '/usr/bin/', '/usr/sbin/', '/usr/lib/',
            '/etc/fstab', '/etc/passwd', '/etc/shadow', '/etc/group'
        ]
        
        for sys_path in system_paths:
            if path.startswith(sys_path):
                return True
        
        return False
    
    def get_block_device_info(self, device: str) -> Optional[Dict[str, any]]:
        """
        Get block device information using lsblk
        
        Args:
            device: Device path (e.g., /dev/sda)
        
        Returns:
            Device information dictionary
        """
        try:
            if not self._command_exists('lsblk'):
                return None
            
            result = subprocess.run(
                ['lsblk', '-J', device],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
            
        except Exception as e:
            print(f"Error getting block device info: {e}")
        
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
            Filesystem type (ext4, btrfs, etc.)
        """
        try:
            partitions = psutil.disk_partitions()
            
            # Find the partition containing this path
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
    
    def sync_filesystem(self):
        """Sync filesystem to ensure data is written to disk"""
        try:
            subprocess.run(['sync'], check=True)
        except Exception as e:
            print(f"Error syncing filesystem: {e}")