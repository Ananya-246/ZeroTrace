"""
Wiping Engine Module
Orchestrates the file wiping process using NIST algorithms
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime
from core.nist_algorithms import NISTAlgorithms
from utils.logging import Logger


class WipingEngine:
    """Main engine for securely wiping files and folders"""
    
    def __init__(self, platform_handler):
        """
        Initialize wiping engine
        
        Args:
            platform_handler: Platform-specific handler
        """
        self.platform_handler = platform_handler
        self.logger = Logger()
        self.nist = NISTAlgorithms()
        self._cancel_requested = False
        self._current_operation = None
    
    def wipe_file(self, file_path: str, method: str = 'clear',
                 progress_callback: Optional[Callable] = None) -> Dict[str, any]:
        """
        Wipe a single file
        
        Args:
            file_path: Path to file to wipe
            method: Wiping method ('clear' or 'purge')
            progress_callback: Optional progress callback function
        
        Returns:
            Dictionary with operation result
        """
        start_time = datetime.now()
        result = {
            'file': file_path,
            'method': method,
            'success': False,
            'error': None,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration': None
        }
        
        try:
            # Validate file exists
            if not Path(file_path).exists():
                result['error'] = 'File does not exist'
                self.logger.log_error(f"File not found: {file_path}")
                return result
            
            # Check if operation was cancelled
            if self._cancel_requested:
                result['error'] = 'Operation cancelled'
                return result
            
            # Get file size for logging
            file_size = Path(file_path).stat().st_size
            self.logger.log_info(f"Wiping file: {file_path} ({file_size} bytes) using {method}")
            
            # Perform the wipe based on method
            if method == 'clear':
                success = self.nist.clear_method(file_path, progress_callback)
            elif method == 'purge':
                success = self.nist.purge_method(file_path, progress_callback=progress_callback)
            else:
                result['error'] = f'Unknown method: {method}'
                self.logger.log_error(result['error'])
                return result
            
            result['success'] = success
            
            # Verify the wipe
            if success:
                verified = self.nist.verify_wipe(file_path)
                result['verified'] = verified
                if not verified:
                    self.logger.log_warning(f"Wipe verification failed: {file_path}")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.log_error(f"Error wiping file {file_path}: {e}")
        
        finally:
            end_time = datetime.now()
            result['end_time'] = end_time.isoformat()
            result['duration'] = (end_time - start_time).total_seconds()
        
        return result
    
    def wipe_folder(self, folder_path: str, method: str = 'clear',
                   recursive: bool = True,
                   progress_callback: Optional[Callable] = None) -> Dict[str, any]:
        """
        Wipe all files in a folder
        
        Args:
            folder_path: Path to folder to wipe
            method: Wiping method ('clear' or 'purge')
            recursive: Whether to wipe subdirectories
            progress_callback: Optional progress callback function
        
        Returns:
            Dictionary with operation results
        """
        start_time = datetime.now()
        result = {
            'folder': folder_path,
            'method': method,
            'recursive': recursive,
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration': None
        }
        
        try:
            folder = Path(folder_path)
            
            if not folder.exists() or not folder.is_dir():
                result['errors'].append('Folder does not exist or is not a directory')
                return result
            
            # Collect all files to wipe
            files_to_wipe = []
            
            if recursive:
                for item in folder.rglob('*'):
                    if item.is_file():
                        files_to_wipe.append(str(item))
            else:
                for item in folder.iterdir():
                    if item.is_file():
                        files_to_wipe.append(str(item))
            
            result['total_files'] = len(files_to_wipe)
            self.logger.log_info(f"Wiping folder: {folder_path} ({result['total_files']} files)")
            
            # Wipe each file
            for idx, file_path in enumerate(files_to_wipe):
                if self._cancel_requested:
                    result['errors'].append('Operation cancelled by user')
                    break
                
                # Update progress
                if progress_callback:
                    overall_progress = (idx / len(files_to_wipe)) * 100
                    progress_callback(overall_progress)
                
                # Wipe the file
                file_result = self.wipe_file(file_path, method)
                
                if file_result['success']:
                    result['successful'] += 1
                else:
                    result['failed'] += 1
                    result['errors'].append({
                        'file': file_path,
                        'error': file_result.get('error', 'Unknown error')
                    })
            
            # Remove empty directories if requested
            if recursive:
                try:
                    self._remove_empty_dirs(folder)
                except Exception as e:
                    self.logger.log_warning(f"Could not remove empty directories: {e}")
            
        except Exception as e:
            result['errors'].append(str(e))
            self.logger.log_error(f"Error wiping folder {folder_path}: {e}")
        
        finally:
            end_time = datetime.now()
            result['end_time'] = end_time.isoformat()
            result['duration'] = (end_time - start_time).total_seconds()
        
        return result
    
    def wipe_selection(self, file_list: List[str], method: str = 'clear',
                      progress_callback: Optional[Callable] = None) -> Dict[str, any]:
        """
        Wipe a selection of files
        
        Args:
            file_list: List of file paths to wipe
            method: Wiping method ('clear' or 'purge')
            progress_callback: Optional progress callback function
        
        Returns:
            Dictionary with operation results
        """
        start_time = datetime.now()
        result = {
            'method': method,
            'total_files': len(file_list),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'files': [],
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration': None
        }
        
        try:
            self.logger.log_info(f"Wiping selection: {len(file_list)} files using {method}")
            
            for idx, file_path in enumerate(file_list):
                if self._cancel_requested:
                    result['skipped'] = len(file_list) - idx
                    break
                
                # Update progress
                if progress_callback:
                    overall_progress = (idx / len(file_list)) * 100
                    progress_callback(overall_progress)
                
                # Wipe the file
                file_result = self.wipe_file(file_path, method)
                result['files'].append(file_result)
                
                if file_result['success']:
                    result['successful'] += 1
                else:
                    result['failed'] += 1
            
        except Exception as e:
            self.logger.log_error(f"Error wiping selection: {e}")
            result['files'].append({'error': str(e)})
        
        finally:
            end_time = datetime.now()
            result['end_time'] = end_time.isoformat()
            result['duration'] = (end_time - start_time).total_seconds()
        
        return result
    
    def emergency_stop(self):
        """Request cancellation of current operation"""
        self._cancel_requested = True
        self.logger.log_warning("Emergency stop requested")
    
    def reset_cancel(self):
        """Reset the cancel flag"""
        self._cancel_requested = False
    
    def _remove_empty_dirs(self, folder: Path):
        """Recursively remove empty directories"""
        for item in folder.iterdir():
            if item.is_dir():
                self._remove_empty_dirs(item)
                try:
                    item.rmdir()  # Only works if directory is empty
                except OSError:
                    pass  # Directory not empty, skip
    
    def estimate_operation_time(self, file_list: List[str], method: str = 'clear') -> float:
        """
        Estimate total time for wiping operation
        
        Args:
            file_list: List of files to wipe
            method: Wiping method
        
        Returns:
            Estimated time in seconds
        """
        total_size = 0
        
        for file_path in file_list:
            try:
                total_size += Path(file_path).stat().st_size
            except (OSError, FileNotFoundError):
                continue
        
        return self.nist.estimate_time(total_size, method)
    
    def get_operation_status(self) -> Dict[str, any]:
        """
        Get current operation status
        
        Returns:
            Dictionary with status information
        """
        return {
            'running': self._current_operation is not None,
            'cancel_requested': self._cancel_requested,
            'current_operation': self._current_operation
        }
    
    def generate_deletion_report(self, results: Dict[str, any]) -> str:
        """
        Generate a deletion report
        
        Args:
            results: Results dictionary from wipe operation
        
        Returns:
            Formatted report string
        """
        report_lines = [
            "=" * 60,
            "SECURE DELETION REPORT",
            "=" * 60,
            f"Operation: {results.get('method', 'Unknown').upper()}",
            f"Start Time: {results.get('start_time', 'N/A')}",
            f"End Time: {results.get('end_time', 'N/A')}",
            f"Duration: {results.get('duration', 0):.2f} seconds",
            "",
            "SUMMARY:",
            f"  Total Files: {results.get('total_files', 0)}",
            f"  Successful: {results.get('successful', 0)}",
            f"  Failed: {results.get('failed', 0)}",
            f"  Skipped: {results.get('skipped', 0)}",
            ""
        ]
        
        # Add errors if any
        if results.get('errors'):
            report_lines.append("ERRORS:")
            for error in results.get('errors', []):
                if isinstance(error, dict):
                    report_lines.append(f"  {error.get('file', 'Unknown')}: {error.get('error', 'Unknown error')}")
                else:
                    report_lines.append(f"  {error}")
            report_lines.append("")
        
        # Add individual file results if available
        if results.get('files'):
            report_lines.append("FILE DETAILS:")
            for file_result in results.get('files', []):
                status = "SUCCESS" if file_result.get('success') else "FAILED"
                report_lines.append(f"  [{status}] {file_result.get('file', 'Unknown')}")
                if not file_result.get('success'):
                    report_lines.append(f"          Error: {file_result.get('error', 'Unknown')}")
        
        report_lines.append("=" * 60)
        
        return '\n'.join(report_lines)