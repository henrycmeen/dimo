import argparse
import subprocess
import sys
from dimo.update_mets import update_dias_mets
from dimo.test import run_test
from dimo.report import generate_report

def update_command(args):
    """Update DIMO to the latest version"""
    print("Updating DIMO to the latest version...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade",
            "git+https://github.com/henrycmeen/dimo.git"
        ])
        print("Successfully updated DIMO!")
    except subprocess.CalledProcessError as e:
        print(f"Error updating DIMO: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="DIMO - Digital Archive Management Tools"
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add update command
    update_parser = subparsers.add_parser('update',
        help='Update DIMO to the latest version')
    
    # update-mets command
    update_parser = subparsers.add_parser('update-mets', 
        help='Update dias-METS file with correct paths, file sizes, and checksums')
    update_parser.add_argument(
        "--mets-file", default="dias-mets.xml",
        help="METS file to update (default: dias-mets.xml)"
    )
    update_parser.add_argument(
        "--content-dir", default="content",
        help="Content directory (default: content)"
    )
    update_parser.add_argument(
        "--dry-run", action="store_true",
        help="Run without writing changes to file (dry run)"
    )
    
    # test command
    test_parser = subparsers.add_parser('test',
        help='Run validation tests for different standards')
    test_parser.add_argument(
        'standard',
        choices=['noark3', 'noark4', 'noark5', 'siard', 'fagsystem'],
        help='Standard to test against'
    )
    test_parser.add_argument(
        "--path", default=".",
        help="Path to the directory containing files to test (default: current directory)"
    )

    # report command
    report_parser = subparsers.add_parser('report',
        help='Generate reports about files and content')
    report_parser.add_argument(
        "--path", default=".",
        help="Path to analyze (default: current directory)"
    )
    report_parser.add_argument(
        "--format", default="text",
        choices=['text', 'json', 'html'],
        help="Output format (default: text)"
    )
    
    args = parser.parse_args()
    
    if args.command == 'update':
        update_command(args)
    elif args.command == 'update-mets':
        update_mets_command(args)
    elif args.command == 'test':
        test_command(args)
    elif args.command == 'report':
        report_command(args)
    elif args.command is None:
        parser.print_help()

if __name__ == "__main__":
    main()