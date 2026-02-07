"""
Verify CLI Module
Command-line interface for file verification operations
"""

import argparse
from pathlib import Path
from typing import List
from utils.helpers import format_file_size


class VerifyCLI:
    """CLI for verifying files and permissions"""
    
    def __init__(self, device_info, validator):
        """
        Initialize verify CLI
        
        Args:
            device_info: DeviceInfo instance
            validator: Validator instance
        """
        self.device_info = device_info
        self.validator = validator
    
    def run(self, args: List[str]):
        """
        Run verify command
        
        Args:
            args: Command-line arguments
        """
        parser = argparse.ArgumentParser(
            description='Verify file accessibility and permissions'
        )
        parser.add_argument(
            '--path',
            type=str,
            required=True,
            help='Path to verify'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information'
        )
        parser.add_argument(
            '--check-integrity',
            action='store_true',
            help='Check file integrity'
        )
        parser.add_argument(
            '--list',
            type=str,
            help='File containing list of paths to verify (one per line)'
        )
        
        parsed_args = parser.parse_args(args)
        
        if parsed_args.list:
            self._verify_list(parsed_args.list)
        else:
            self._verify_single(
                parsed_args.path,
                parsed_args.detailed,
                parsed_args.check_integrity
            )
    
    def _verify_single(self, path: str, detailed: bool = False,
                      check_integrity: bool = False):
        """Verify a single file or directory"""
        print(f"\nVerifying: {path}\n")
        
        # Basic path validation
        validation = self.validator.validate_path(path)
        
        print("=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)
        
        if validation['valid']:
            print("✓ Path is VALID")
            print(f"  Type: {validation['type']}")
            print(f"  Exists: {validation['exists']}")
            print(f"  Accessible: {validation['accessible']}")
        else:
            print("✗ Path is INVALID")
            for error in validation['errors']:
                print(f"  Error: {error}")
            return
        
        # Permission check
        perm_check = self.validator.validate_permissions(path)
        
        print("\nPERMISSIONS:")
        print(f"  Readable: {'✓' if perm_check['readable'] else '✗'}")
        print(f"  Writable: {'✓' if perm_check['writable'] else '✗'}")
        print(f"  Parent Writable: {'✓' if perm_check['parent_writable'] else '✗'}")
        print(f"  Can Delete: {'✓' if perm_check['can_delete'] else '✗'}")
        
        if perm_check['errors']:
            print("\n  Permission Issues:")
            for error in perm_check['errors']:
                print(f"    - {error}")
        
        # Detailed information
        if detailed and validation['type'] == 'file':
            self._show_detailed_info(path)
        
        # Integrity check
        if check_integrity and validation['type'] == 'file':
            print("\nINTEGRITY CHECK:")
            if self.device_info.verify_file_integrity(path):
                print("  ✓ File integrity verified")
            else:
                print("  ✗ File integrity check failed")
        
        print("=" * 60)
    
    def _show_detailed_info(self, path: str):
        """Show detailed file information"""
        info = self.device_info.get_detailed_file_info(path)
        
        if 'error' in info:
            print(f"\nError getting details: {info['error']}")
            return
        
        print("\nDETAILED INFORMATION:")
        print(f"  Name: {info.get('name', 'N/A')}")
        print(f"  Size: {info.get('size_formatted', 'N/A')}")
        print(f"  Type: {info.get('type', 'N/A')}")
        print(f"  Extension: {info.get('extension', 'N/A')}")
        print(f"  Modified: {info.get('modified', 'N/A')}")
        print(f"  Created: {info.get('created', 'N/A')}")
        
        # Platform-specific info
        if 'platform_specific' in info:
            print("\n  Platform-Specific Attributes:")
            for key, value in info['platform_specific'].items():
                print(f"    {key}: {value}")
    
    def _verify_list(self, list_file: str):
        """Verify a list of files from a file"""
        try:
            with open(list_file, 'r') as f:
                paths = [line.strip() for line in f if line.strip()]
            
            if not paths:
                print("ERROR: Empty file list")
                return
            
            print(f"\nVerifying {len(paths)} file(s)...\n")
            
            # Validate the selection
            from platform import get_platform_handler
            platform_handler = get_platform_handler()
            
            result = self.validator.validate_selection(paths, platform_handler)
            
            print("=" * 60)
            print("BATCH VERIFICATION RESULTS")
            print("=" * 60)
            print(f"Total Files: {result['total_files']}")
            print(f"Valid Files: {len(result['valid_files'])}")
            print(f"Invalid Files: {len(result['invalid_files'])}")
            print(f"System Files: {len(result['system_files'])}")
            
            if result['warnings']:
                print("\nWARNINGS:")
                for warning in result['warnings'][:10]:  # Limit warnings
                    print(f"  ⚠ {warning}")
                if len(result['warnings']) > 10:
                    print(f"  ... and {len(result['warnings']) - 10} more warnings")
            
            if result['errors']:
                print("\nERRORS:")
                for error in result['errors']:
                    print(f"  ✗ {error}")
            
            # Show invalid files
            if result['invalid_files']:
                print("\nINVALID FILES:")
                for invalid in result['invalid_files'][:10]:
                    print(f"  {invalid['path']}")
                    for reason in invalid['reasons']:
                        print(f"    - {reason}")
                if len(result['invalid_files']) > 10:
                    print(f"  ... and {len(result['invalid_files']) - 10} more")
            
            # Safety check
            safety = self.validator.validate_file_list_safety(result['valid_files'])
            
            if safety['critical_warnings']:
                print("\nCRITICAL WARNINGS:")
                for warning in safety['critical_warnings']:
                    print(f"  ⚠⚠⚠ {warning}")
            
            print("\nSTATISTICS:")
            stats = safety['statistics']
            print(f"  Total Size: {format_file_size(stats['total_size'])}")
            print(f"  Large Files (>1GB): {stats['large_files']}")
            print(f"  Hidden Files: {stats['hidden_files']}")
            print(f"  Executable Files: {stats['executable_files']}")
            
            print("=" * 60)
            
            # Overall verdict
            if result['valid']:
                print("\n✓ File list is VALID and ready for wiping")
            else:
                print("\n✗ File list contains ERRORS - resolve issues before wiping")
            
        except FileNotFoundError:
            print(f"ERROR: File not found: {list_file}")
        except Exception as e:
            print(f"ERROR: {e}")