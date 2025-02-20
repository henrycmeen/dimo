import os
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

def generate_report(path=".", format="text"):
    """
    Generate a report about files and content in the specified directory
    """
    stats = {
        'total_files': 0,
        'total_size': 0,
        'extensions': Counter(),
        'size_ranges': defaultdict(int),
        'largest_files': [],
        'newest_files': [],
        'oldest_files': []
    }
    
    # Define size ranges in bytes
    size_ranges = [
        (0, 1024, "0-1KB"),
        (1024, 1024*1024, "1KB-1MB"),
        (1024*1024, 1024*1024*1024, "1MB-1GB"),
        (1024*1024*1024, float('inf'), ">1GB")
    ]
    
    # Collect statistics
    for filepath in Path(path).rglob('*'):
        if filepath.is_file():
            file_size = filepath.stat().st_size
            file_time = filepath.stat().st_mtime
            
            stats['total_files'] += 1
            stats['total_size'] += file_size
            stats['extensions'][filepath.suffix.lower() or 'no_extension'] += 1
            
            # Categorize by size range
            for start, end, label in size_ranges:
                if start <= file_size < end:
                    stats['size_ranges'][label] += 1
                    break
            
            # Track largest files (keep top 10)
            stats['largest_files'].append((filepath, file_size))
            stats['largest_files'].sort(key=lambda x: x[1], reverse=True)
            stats['largest_files'] = stats['largest_files'][:10]
            
            # Track newest and oldest files
            stats['newest_files'].append((filepath, file_time))
            stats['oldest_files'].append((filepath, file_time))
            
    stats['newest_files'].sort(key=lambda x: x[1], reverse=True)
    stats['oldest_files'].sort(key=lambda x: x[1])
    stats['newest_files'] = stats['newest_files'][:5]
    stats['oldest_files'] = stats['oldest_files'][:5]
            
    # Output report based on format
    if format == "text":
        print("\n=== Directory Analysis Report ===")
        print(f"Path: {path}")
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n=== Summary ===")
        print(f"Total Files: {stats['total_files']:,}")
        print(f"Total Size: {_format_size(stats['total_size'])}")
        
        print("\n=== File Sizes ===")
        for label, count in stats['size_ranges'].items():
            percentage = (count / stats['total_files'] * 100) if stats['total_files'] > 0 else 0
            print(f"{label}: {count:,} files ({percentage:.1f}%)")
        
        print("\n=== File Extensions ===")
        for ext, count in stats['extensions'].most_common(10):
            percentage = (count / stats['total_files'] * 100)
            print(f"{ext}: {count:,} files ({percentage:.1f}%)")
        
        print("\n=== Largest Files ===")
        for filepath, size in stats['largest_files'][:5]:
            print(f"{filepath.name}: {_format_size(size)}")
        
        print("\n=== Newest Files ===")
        for filepath, mtime in stats['newest_files'][:5]:
            timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{filepath.name}: {timestamp}")
    
    # TODO: Implement JSON and HTML output formats

def _format_size(size):
    """Convert size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:,.1f} {unit}"
        size /= 1024.0