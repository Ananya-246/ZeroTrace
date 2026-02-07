"""
Wipe CLI Module
Command-line interface for secure file wiping operations
"""

import argparse
import sys
from pathlib import Path
from typing import List
from utils.helpers import format_file_size, format_time


class WipeCLI:
    """CLI for wiping files"""
    
    def __init__(self, wiping_engine, validator):
        """
        Initialize wipe CLI
        
        Args:
            wiping_engine: WipingEngine instance
            validator: Validator instance
        """
        self.wiping_engine = wiping_engine
        self.validator = validator
    
    def run(self, args: List[str]):
        """
        Run wipe command
        
        Args:
            args: Command-line arguments
        """
        parser = argparse.ArgumentParser(
            description='Securely wipe files using NIST algorithms'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Single file to wipe'
        )
        parser.add_argument(
            '--folder',
            type=str,
            help='Folder to wipe (all files)'
        )
        parser.add_argument(
            '--list',
            type=str,
            help='File containing list of paths to wipe (one per line)'
        )
        parser.add_argument(
            '--method',
            type=str,
            choices=['clear', 'purge'],
            default='clear',
            help='Wiping method: clear (fast) or purge (secure)'
        )
        parser.add_argument(
            '--recursive',
            action='store_true',
            default=True,
            help='Recursively wipe folder contents'
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Skip confirmation prompt'
        )
        parser.add_argument(
            '--report',
            type=str,
            help='Save deletion report to file'
        )
        
        parsed_args = parser.parse_args(args)
        
        # Validate method
        if not self.validator.validate_wipe_method(parsed_args.method):
            print(f"ERROR: Invalid wipe method: {parsed_args.method}")
            return
        
        # Determine what to wipe
        if parsed_args.file:
            self._wipe_single_file(
                parsed_args.file,
                parsed_args.method,
                parsed_args.yes,
                parsed_args.report
            )
        elif parsed_args.folder:
            self._wipe_folder(
                parsed_args.folder,
                parsed_args.method,
                parsed_args.recursive,
                parsed_args.yes,
                parsed_args.report
            )
        elif parsed_args.list:
            self._wipe_list(
                parsed_args.list,
                parsed_args.method,
                parsed_args.yes,
                parsed_args.report
            )
        else:
            print("ERROR: Must specify --file, --folder, or --list")
            parser.print_help()
    
    def _wipe_single_file(self, file_path: str, method: str,
                         skip_confirmation: bool, report_file: str = None):
        """Wipe a single file"""
        # Validate path
        validation = self.validator.validate_path(file_path)
        if not validation['valid']:
            print(f"ERROR: Invalid path: {file_path}")
            for error in validation['errors']:
                print(f"  - {error}")
            return
        
        # Validate permissions
        perm_check = self.validator.validate_permissions(file_path)
        if not perm_check['can_delete']:
            print(f"ERROR: Cannot delete file: {file_path}")
            for error in perm_check['errors']:
                print(f"  - {error}")
            return
        
        # Get file info
        size = Path(file_path).stat().st_size
        
        # Show warning
        print("\n" + "=" * 60)
        print("SECURE FILE WIPE")
        print("=" * 60)
        print(f"File: {file_path}")
        print(f"Size: {format_file_size(size)}")
        print(f"Method: {method.upper()}")
        
        # Estimate time
        estimate = self.wiping_engine.nist.estimate_time(size, method)
        print(f"Estimated Time: {format_time(estimate)}")
        print("=" * 60)
        
        # Confirmation
        if not skip_confirmation:
            response = input("\n⚠ This operation is IRREVERSIBLE. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Operation cancelled.")
                return
        
        # Perform wipe
        print("\nWiping file... (Press Ctrl+C to abort)\n")
        
        try:
            def progress_callback(percent):
                print(f"\rProgress: {percent:.1f}%", end='', flush=True)
            
            result = self.wiping_engine.wipe_file(
                file_path,
                method,
                progress_callback
            )
            
            print("\n")  # New line after progress
            
            # Show result
            if result['success']:
                print("✓ File successfully wiped!")
                if result.get('verified'):
                    print("✓ Deletion verified")
            else:
                print(f"✗ Wiping failed: {result.get('error', 'Unknown error')}")
            
            # Save report if requested
            if report_file:
                self._save_single_file_report(result, report_file)
        
        except KeyboardInterrupt:
            print("\n\n⚠ Operation cancelled by user")
            self.wiping_engine.emergency_stop()
    
    def _wipe_folder(self, folder_path: str, method: str, recursive: bool,
                    skip_confirmation: bool, report_file: str = None):
        """Wipe all files in a folder"""
        # Validate path
        validation = self.validator.validate_path(folder_path)
        if not validation['valid'] or validation['type'] != 'directory':
            print(f"ERROR: Invalid folder: {folder_path}")
            return
        
        print(f"\nScanning folder: {folder_path}...")
        
        # Count files
        from core.device_discovery import DeviceDiscovery
        from platform import get_platform_handler
        
        discovery = DeviceDiscovery(get_platform_handler())
        files = discovery.scan_directory(folder_path, recursive)
        
        if not files:
            print("No files found in folder.")
            return
        
        total_size = discovery.get_total_size(files)
        
        # Show warning
        print("\n" + "=" * 60)
        print("SECURE FOLDER WIPE")
        print("=" * 60)
        print(f"Folder: {folder_path}")
        print(f"Files: {len(files)}")
        print(f"Total Size: {format_file_size(total_size)}")
        print(f"Method: {method.upper()}")
        print(f"Recursive: {'Yes' if recursive else 'No'}")
        
        estimate = self.wiping_engine.nist.estimate_time(total_size, method)
        print(f"Estimated Time: {format_time(estimate)}")
        print("=" * 60)
        
        # Confirmation
        if not skip_confirmation:
            response = input("\n⚠ This will DELETE ALL FILES in the folder. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Operation cancelled.")
                return
        
        # Perform wipe
        print("\nWiping folder... (Press Ctrl+C to abort)\n")
        
        try:
            def progress_callback(percent):
                print(f"\rOverall Progress: {percent:.1f}%", end='', flush=True)
            
            result = self.wiping_engine.wipe_folder(
                folder_path,
                method,
                recursive,
                progress_callback
            )
            
            print("\n")  # New line after progress
            
            # Show results
            self._display_results(result)
            
            # Save report if requested
            if report_file:
                self._save_report(result, report_file)
        
        except KeyboardInterrupt:
            print("\n\n⚠ Operation cancelled by user")
            self.wiping_engine.emergency_stop()
    
    def _wipe_list(self, list_file: str, method: str,
                  skip_confirmation: bool, report_file: str = None):
        """Wipe files from a list"""
        try:
            with open(list_file, 'r') as f:
                paths = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"ERROR: File not found: {list_file}")
            return
        except Exception as e:
            print(f"ERROR reading file list: {e}")
            return
        
        if not paths:
            print("ERROR: Empty file list")
            return
        
        # Validate paths
        from platform import get_platform_handler
        platform_handler = get_platform_handler()
        
        validation = self.validator.validate_selection(paths, platform_handler)
        
        if not validation['valid']:
            print("ERROR: File list validation failed")
            for error in validation['errors']:
                print(f"  - {error}")
            return
        
        valid_paths = validation['valid_files']
        
        # Calculate total size
        total_size = 0
        for path in valid_paths:
            try:
                total_size += Path(path).stat().st_size
            except Exception:
                continue
        
        # Show warning
        print("\n" + "=" * 60)
        print("SECURE BATCH WIPE")
        print("=" * 60)
        print(f"Files: {len(valid_paths)}")
        print(f"Total Size: {format_file_size(total_size)}")
        print(f"Method: {method.upper()}")
        
        estimate = self.wiping_engine.nist.estimate_time(total_size, method)
        print(f"Estimated Time: {format_time(estimate)}")
        print("=" * 60)
        
        # Confirmation
        if not skip_confirmation:
            response = input("\n⚠ This operation is IRREVERSIBLE. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Operation cancelled.")
                return
        
        # Perform wipe
        print("\nWiping files... (Press Ctrl+C to abort)\n")
        
        try:
            def progress_callback(percent):
                print(f"\rOverall Progress: {percent:.1f}%", end='', flush=True)
            
            result = self.wiping_engine.wipe_selection(
                valid_paths,
                method,
                progress_callback
            )
            
            print("\n")  # New line after progress
            
            # Show results
            self._display_results(result)
            
            # Save report if requested
            if report_file:
                self._save_report(result, report_file)
        
        except KeyboardInterrupt:
            print("\n\n⚠ Operation cancelled by user")
            self.wiping_engine.emergency_stop()
    
    def _display_results(self, result: dict):
        """Display operation results"""
        print("=" * 60)
        print("OPERATION COMPLETE")
        print("=" * 60)
        print(f"Total Files: {result.get('total_files', 0)}")
        print(f"Successful: {result.get('successful', 0)} ✓")
        print(f"Failed: {result.get('failed', 0)} ✗")
        if result.get('skipped', 0) > 0:
            print(f"Skipped: {result.get('skipped', 0)}")
        print(f"Duration: {format_time(result.get('duration', 0))}")
        print("=" * 60)
        
        # Show errors if any
        if result.get('errors'):
            print("\nERRORS:")
            for error in result['errors'][:5]:  # Limit to 5 errors
                if isinstance(error, dict):
                    print(f"  {error.get('file', 'Unknown')}: {error.get('error', 'Unknown')}")
                else:
                    print(f"  {error}")
            if len(result['errors']) > 5:
                print(f"  ... and {len(result['errors']) - 5} more errors")
    
    def _save_report(self, result: dict, report_file: str):
        """Save operation report to file"""
        try:
            report = self.wiping_engine.generate_deletion_report(result)
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            print(f"\n✓ Report saved to: {report_file}")
        except Exception as e:
            print(f"\n✗ Error saving report: {e}")
    
    def _save_single_file_report(self, result: dict, report_file: str):
        """Save single file wipe report"""
        try:
            report_lines = [
                "=" * 60,
                "SECURE FILE WIPE REPORT",
                "=" * 60,
                f"File: {result.get('file', 'Unknown')}",
                f"Method: {result.get('method', 'Unknown').upper()}",
                f"Success: {result.get('success', False)}",
                f"Verified: {result.get('verified', False)}",
                f"Start Time: {result.get('start_time', 'N/A')}",
                f"End Time: {result.get('end_time', 'N/A')}",
                f"Duration: {format_time(result.get('duration', 0))}",
                "=" * 60
            ]
            
            if result.get('error'):
                report_lines.append(f"\nError: {result['error']}")
            
            with open(report_file, 'w') as f:
                f.write('\n'.join(report_lines))
            
            print(f"\n✓ Report saved to: {report_file}")
        except Exception as e:
            print(f"\n✗ Error saving report: {e}")