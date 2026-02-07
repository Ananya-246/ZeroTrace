"""
Logging Module
Comprehensive logging system for audit trails and debugging
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


class Logger:
    """Enhanced logger for the secure wipe application"""
    
    def __init__(self, name: str = 'SecureWipe'):
        """
        Initialize logger
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.audit_log = []
    
    def log_info(self, message: str):
        """Log informational message"""
        self.logger.info(message)
        self._add_to_audit('INFO', message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
        self._add_to_audit('WARNING', message)
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
        self._add_to_audit('ERROR', message)
    
    def log_debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
        self._add_to_audit('DEBUG', message)
    
    def log_critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
        self._add_to_audit('CRITICAL', message)
    
    def log_discovery(self, files_found: int, total_size: int = 0):
        """
        Log discovery operation
        
        Args:
            files_found: Number of files discovered
            total_size: Total size in bytes
        """
        from utils.helpers import format_file_size
        
        message = f"Discovery: Found {files_found} files"
        if total_size > 0:
            message += f" totaling {format_file_size(total_size)}"
        
        self.log_info(message)
    
    def log_user_selection(self, selected_files: List[str]):
        """
        Log user file selection
        
        Args:
            selected_files: List of selected file paths
        """
        self.log_info(f"User selected {len(selected_files)} file(s) for deletion")
        
        # Log first few files
        for file_path in selected_files[:10]:
            self.log_debug(f"  Selected: {file_path}")
        
        if len(selected_files) > 10:
            self.log_debug(f"  ... and {len(selected_files) - 10} more files")
    
    def log_wipe_progress(self, file_path: str, status: str, percent: float = None):
        """
        Log wiping progress
        
        Args:
            file_path: File being wiped
            status: Status message
            percent: Completion percentage
        """
        if percent is not None:
            message = f"Wiping {file_path}... {percent:.1f}% - {status}"
        else:
            message = f"Wiping {file_path}... {status}"
        
        self.log_debug(message)
    
    def log_completion(self, results: Dict[str, any]):
        """
        Log operation completion
        
        Args:
            results: Results dictionary
        """
        message = (
            f"Operation completed: "
            f"{results.get('successful', 0)} successful, "
            f"{results.get('failed', 0)} failed"
        )
        
        if results.get('skipped', 0) > 0:
            message += f", {results.get('skipped', 0)} skipped"
        
        self.log_info(message)
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive audit report
        
        Returns:
            Report as string
        """
        report_lines = [
            "=" * 80,
            "SECURE WIPE AUDIT LOG",
            "=" * 80,
            f"Generated: {datetime.now().isoformat()}",
            f"Total log entries: {len(self.audit_log)}",
            "",
            "LOG ENTRIES:",
            "-" * 80
        ]
        
        for entry in self.audit_log:
            timestamp = entry['timestamp']
            level = entry['level']
            message = entry['message']
            report_lines.append(f"[{timestamp}] [{level:8}] {message}")
        
        report_lines.append("=" * 80)
        
        return '\n'.join(report_lines)
    
    def save_audit_log(self, output_path: str = None) -> str:
        """
        Save audit log to file
        
        Args:
            output_path: Path to save log file
        
        Returns:
            Path to saved log file
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'audit_log_{timestamp}.txt'
        
        report = self.generate_report()
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        self.log_info(f"Audit log saved to {output_path}")
        return output_path
    
    def _add_to_audit(self, level: str, message: str):
        """Add entry to audit log"""
        self.audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        })
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get logging statistics
        
        Returns:
            Dictionary with log level counts
        """
        stats = {
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'DEBUG': 0,
            'CRITICAL': 0,
            'TOTAL': len(self.audit_log)
        }
        
        for entry in self.audit_log:
            level = entry['level']
            if level in stats:
                stats[level] += 1
        
        return stats
    
    def clear_audit_log(self):
        """Clear the audit log"""
        self.audit_log.clear()
        self.log_info("Audit log cleared")


def setup_logging(log_file: Optional[str] = None, 
                 level: int = logging.INFO,
                 console: bool = True):
    """
    Set up the logging configuration
    
    Args:
        log_file: Optional log file path
        level: Logging level (default: INFO)
        console: Whether to log to console
    """
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Default log file
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'securewipe_{timestamp}.log'
    
    # Configure root logger
    handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    handlers.append(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        handlers=handlers
    )
    
    logging.info(f"Logging initialized - Log file: {log_file}")


class AuditLogger:
    """Specialized logger for compliance and audit trails"""
    
    def __init__(self, audit_file: str = None):
        """
        Initialize audit logger
        
        Args:
            audit_file: Path to audit file
        """
        if not audit_file:
            audit_dir = Path('audit')
            audit_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d')
            audit_file = audit_dir / f'audit_{timestamp}.log'
        
        self.audit_file = audit_file
        self.entries = []
    
    def log_operation(self, operation: str, details: Dict[str, any]):
        """
        Log an operation for audit trail
        
        Args:
            operation: Operation type
            details: Operation details
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'details': details
        }
        
        self.entries.append(entry)
        self._write_to_file(entry)
    
    def _write_to_file(self, entry: Dict[str, any]):
        """Write entry to audit file"""
        import json
        
        with open(self.audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_audit_trail(self) -> List[Dict[str, any]]:
        """Get all audit entries"""
        return self.entries.copy()