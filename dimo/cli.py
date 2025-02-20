import argparse
from App.update_mets import update_dias_mets

def update_mets_command(args):
    update_dias_mets(args.mets_file, args.content_dir, dry_run=args.dry_run)

def main():
    parser = argparse.ArgumentParser(
        description="DIMO - Digital Archive Management Tools"
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
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
    
    args = parser.parse_args()
    
    if args.command == 'update-mets':
        update_mets_command(args)
    elif args.command is None:
        parser.print_help()

if __name__ == "__main__":
    main()