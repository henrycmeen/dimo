# DIMO - Digital Archive Management Tools

A tool for managing digital archives, with features including:

- Update METS files with correct paths, file sizes, and checksums

## Installation

```bash
pip install git+https://github.com/henrycmeen/dimo.git
```

## Usage

Update METS file:
```bash
dimo update-mets
```

Optional arguments:
- `--mets-file`: Path to METS file (default: dias-mets.xml)
- `--content-dir`: Content directory path (default: content)
- `--dry-run`: Run without making changes

