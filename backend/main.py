#!/usr/bin/env python3
"""
Secure Data Wiping Tool - Main Entry Point
Detects OS, initializes components, and launches the interface
"""

import sys
import platform
import logging
from pathlib import Path

# Import core modules
from core.device_discovery import DeviceDiscovery
from core.device_info import DeviceInfo
from core.wiping_engine import WipingEngine
from utils.logging import setup_logging, Logger
from utils.validation import Validator

# Import platform-specific modules
from platforms import get_platform_handler


class SecureWipeApp:
    """Main application controller"""
    
    def __init__(self):
        """Initialize the application"""
        self.logger = Logger()
        self.os_type = platform.system()
        self.platform_handler = None
        self.discovery = None
        self.device_info = None
        self.wiping_engine = None
        self.validator = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all application components"""
        try:
            # Set up logging
            setup_logging()
            self.logger.log_info(f"Starting Secure Wipe Tool on {self.os_type}")
            
            # Get platform-specific handler
            self.platform_handler = get_platform_handler()
            self.logger.log_info(f"Platform handler loaded: {type(self.platform_handler).__name__}")
            
            # Initialize core components
            self.discovery = DeviceDiscovery(self.platform_handler)
            self.device_info = DeviceInfo(self.platform_handler)
            self.wiping_engine = WipingEngine(self.platform_handler)
            self.validator = Validator()
            
            self.logger.log_info("All components initialized successfully")
            
        except Exception as e:
            self.logger.log_error(f"Failed to initialize components: {e}")
            raise
    
    def run_cli(self):
        """Run in command-line interface mode"""
        from cli.discover import DiscoverCLI
        from cli.verify import VerifyCLI
        from cli.wipe import WipeCLI
        
        print("=" * 60)
        print("SECURE DATA WIPING TOOL - CLI Mode")
        print("=" * 60)
        
        if len(sys.argv) < 2:
            self._show_cli_help()
            return
        
        command = sys.argv[1].lower()
        
        if command == "discover":
            cli = DiscoverCLI(self.discovery, self.device_info)
            cli.run(sys.argv[2:])
        elif command == "verify":
            cli = VerifyCLI(self.device_info, self.validator)
            cli.run(sys.argv[2:])
        elif command == "wipe":
            cli = WipeCLI(self.wiping_engine, self.validator)
            cli.run(sys.argv[2:])
        else:
            print(f"Unknown command: {command}")
            self._show_cli_help()
    
    def run_gui(self):
        """Run in graphical interface mode"""
        try:
            import tkinter as tk
            from gui.main_window import MainWindow
            
            self.logger.log_info("Starting GUI mode")
            
            root = tk.Tk()
            app = MainWindow(
                root,
                self.discovery,
                self.device_info,
                self.wiping_engine,
                self.validator,
                self.logger
            )
            root.mainloop()
            
        except ImportError:
            print("ERROR: GUI dependencies not available. Please install tkinter.")
            print("Falling back to CLI mode...")
            self.run_cli()
        except Exception as e:
            self.logger.log_error(f"GUI error: {e}")
            raise
    
    def _show_cli_help(self):
        """Display CLI help information"""
        help_text = """
Usage: python main.py <command> [options]

Commands:
  discover [--path PATH]              Scan and list all files
  verify [--path PATH]                Verify file accessibility
  wipe [--file FILE] [--method METHOD] Securely delete files
  
Examples:
  python main.py discover --path /home/user
  python main.py verify --path /
  python main.py wipe --file /path/to/file.txt --method purge
  
Wipe Methods:
  clear  - Single-pass overwrite (faster, NIST Clear)
  purge  - Multi-pass overwrite (slower, NIST Purge)
"""
        print(help_text)


def main():
    """Main entry point"""
    try:
        app = SecureWipeApp()
        
        # Check if running from USB (optional boot check)
        # This would detect if booted from USB vs. installed on system
        
        # Determine mode (GUI vs CLI)
        if len(sys.argv) > 1 and sys.argv[1] in ['discover', 'verify', 'wipe']:
            # CLI mode
            app.run_cli()
        else:
            # GUI mode (default)
            app.run_gui()
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()