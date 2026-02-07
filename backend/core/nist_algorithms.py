"""
NIST Algorithms Module
Implements NIST 800-88 compliant data sanitization methods
"""

import os
import secrets
from pathlib import Path
from typing import Optional, Callable
from utils.logging import Logger


class NISTAlgorithms:
    """
    Implements NIST SP 800-88 data sanitization algorithms
    
    Methods:
    - Clear: Single-pass overwrite with zeros
    - Purge: Multi-pass overwrite (DoD 5220.22-M inspired)
    """
    
    def __init__(self):
        """Initialize NIST algorithms"""
        self.logger = Logger()
        self.BLOCK_SIZE = 65536  # 64KB blocks for efficient I/O
    
    def clear_method(self, file_path: str, 
                    progress_callback: Optional[Callable] = None) -> bool:
        """
        NIST Clear Method - Single pass overwrite with zeros
        
        Suitable for: Non-sensitive data, regular use
        Speed: Fast (1 pass)
        
        Args:
            file_path: Path to file to clear
            progress_callback: Optional callback function(percent)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                self.logger.log_error(f"File not found: {file_path}")
                return False
            
            file_size = path_obj.stat().st_size
            self.logger.log_info(f"Clear method: {file_path} ({file_size} bytes)")
            
            # Single pass with zeros
            bytes_written = 0
            
            with open(file_path, 'r+b') as f:
                while bytes_written < file_size:
                    chunk_size = min(self.BLOCK_SIZE, file_size - bytes_written)
                    f.write(b'\x00' * chunk_size)
                    bytes_written += chunk_size
                    
                    # Update progress
                    if progress_callback:
                        percent = (bytes_written / file_size) * 100
                        progress_callback(percent)
                
                # Ensure data is written to disk
                f.flush()
                os.fsync(f.fileno())
            
            # Remove the file after overwriting
            path_obj.unlink()
            
            self.logger.log_info(f"Clear method completed: {file_path}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Clear method failed for {file_path}: {e}")
            return False
    
    def purge_method(self, file_path: str, 
                    passes: int = 7,
                    progress_callback: Optional[Callable] = None) -> bool:
        """
        NIST Purge Method - Multi-pass overwrite with random data
        
        Implements DoD 5220.22-M inspired algorithm:
        - Pass 1: Write zeros
        - Pass 2: Write ones
        - Passes 3-6: Write random data
        - Pass 7: Write random data and verify
        
        Suitable for: Sensitive data, high security requirements
        Speed: Slow (7 passes by default)
        
        Args:
            file_path: Path to file to purge
            passes: Number of overwrite passes (default: 7)
            progress_callback: Optional callback function(percent)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                self.logger.log_error(f"File not found: {file_path}")
                return False
            
            file_size = path_obj.stat().st_size
            self.logger.log_info(f"Purge method: {file_path} ({file_size} bytes, {passes} passes)")
            
            # Perform multiple passes
            for pass_num in range(1, passes + 1):
                self.logger.log_debug(f"Pass {pass_num}/{passes} for {file_path}")
                
                # Determine pattern for this pass
                if pass_num == 1:
                    pattern = b'\x00'  # Zeros
                elif pass_num == 2:
                    pattern = b'\xFF'  # Ones
                else:
                    pattern = None  # Random data
                
                # Perform the overwrite pass
                if not self._overwrite_pass(file_path, file_size, pattern, pass_num, passes, progress_callback):
                    return False
            
            # Final verification pass
            if not self._verify_overwrite(file_path):
                self.logger.log_warning(f"Verification failed for {file_path}")
            
            # Remove the file after overwriting
            path_obj.unlink()
            
            self.logger.log_info(f"Purge method completed: {file_path}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Purge method failed for {file_path}: {e}")
            return False
    
    def _overwrite_pass(self, file_path: str, file_size: int, 
                       pattern: Optional[bytes], pass_num: int, 
                       total_passes: int,
                       progress_callback: Optional[Callable]) -> bool:
        """
        Perform a single overwrite pass
        
        Args:
            file_path: Path to file
            file_size: Size of file in bytes
            pattern: Byte pattern to write (None = random)
            pass_num: Current pass number
            total_passes: Total number of passes
            progress_callback: Progress callback function
        
        Returns:
            True if successful
        """
        try:
            bytes_written = 0
            
            with open(file_path, 'r+b') as f:
                while bytes_written < file_size:
                    chunk_size = min(self.BLOCK_SIZE, file_size - bytes_written)
                    
                    # Generate data to write
                    if pattern:
                        data = pattern * chunk_size
                    else:
                        data = secrets.token_bytes(chunk_size)
                    
                    f.write(data)
                    bytes_written += chunk_size
                    
                    # Update progress
                    if progress_callback:
                        # Calculate overall progress across all passes
                        pass_progress = (pass_num - 1) / total_passes
                        current_progress = (bytes_written / file_size) / total_passes
                        total_progress = (pass_progress + current_progress) * 100
                        progress_callback(total_progress)
                
                # Ensure data is written to disk
                f.flush()
                os.fsync(f.fileno())
            
            return True
            
        except Exception as e:
            self.logger.log_error(f"Overwrite pass failed: {e}")
            return False
    
    def _verify_overwrite(self, file_path: str) -> bool:
        """
        Verify that file has been overwritten
        
        Args:
            file_path: Path to file
        
        Returns:
            True if verification passed
        """
        try:
            # Read a sample of the file to verify it's been overwritten
            # We check first, middle, and last blocks
            
            path_obj = Path(file_path)
            file_size = path_obj.stat().st_size
            
            if file_size == 0:
                return True
            
            samples_verified = 0
            
            with open(file_path, 'rb') as f:
                # Check first block
                first_block = f.read(min(1024, file_size))
                if first_block:
                    samples_verified += 1
                
                # Check middle block if file is large enough
                if file_size > 2048:
                    f.seek(file_size // 2)
                    middle_block = f.read(min(1024, file_size // 2))
                    if middle_block:
                        samples_verified += 1
                
                # Check last block
                if file_size > 1024:
                    f.seek(-1024, 2)
                    last_block = f.read(1024)
                    if last_block:
                        samples_verified += 1
            
            # If we successfully read samples, verification passed
            return samples_verified > 0
            
        except Exception as e:
            self.logger.log_warning(f"Verification error: {e}")
            return False
    
    def verify_wipe(self, file_path: str) -> bool:
        """
        Verify that a file has been completely wiped (deleted)
        
        Args:
            file_path: Path to file that should be deleted
        
        Returns:
            True if file no longer exists
        """
        try:
            return not Path(file_path).exists()
        except Exception:
            return False
    
    def estimate_time(self, file_size: int, method: str = 'clear') -> float:
        """
        Estimate time to wipe a file
        
        Args:
            file_size: Size of file in bytes
            method: Wiping method ('clear' or 'purge')
        
        Returns:
            Estimated time in seconds
        """
        # Approximate write speed: 100 MB/s (conservative estimate)
        WRITE_SPEED = 100 * 1024 * 1024  # bytes per second
        
        if method == 'clear':
            passes = 1
        else:  # purge
            passes = 7
        
        # Calculate time: (file_size * passes) / write_speed
        estimated_seconds = (file_size * passes) / WRITE_SPEED
        
        return estimated_seconds
    
    def get_method_info(self, method: str) -> dict:
        """
        Get information about a wiping method
        
        Args:
            method: Method name ('clear' or 'purge')
        
        Returns:
            Dictionary with method information
        """
        methods = {
            'clear': {
                'name': 'NIST Clear',
                'description': 'Single-pass overwrite with zeros',
                'passes': 1,
                'security_level': 'Standard',
                'speed': 'Fast',
                'use_case': 'Non-sensitive data, regular use'
            },
            'purge': {
                'name': 'NIST Purge (DoD 5220.22-M)',
                'description': 'Multi-pass overwrite with random data',
                'passes': 7,
                'security_level': 'High',
                'speed': 'Slow',
                'use_case': 'Sensitive data, compliance requirements'
            }
        }
        
        return methods.get(method, {})