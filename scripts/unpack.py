#!/usr/bin/env python3
"""
Unpack script for air-gapped deployment.
Extracts archive, runs database migrations, and builds frontend.
"""

import zipfile
import json
import subprocess
import sys
from pathlib import Path


def find_latest_archive(builds_dir):
    """Find the most recent archive in builds directory."""
    archives = list(builds_dir.glob('mailseller-*.zip'))
    if not archives:
        print(f"Error: No archives found in {builds_dir}")
        sys.exit(1)

    # Sort by modification time, newest first
    latest = max(archives, key=lambda p: p.stat().st_mtime)
    return latest


def extract_manifest(archive_path):
    """Extract and parse manifest from archive."""
    try:
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            if 'MANIFEST.json' not in zipf.namelist():
                print("Warning: No manifest found in archive")
                return None

            manifest_data = zipf.read('MANIFEST.json')
            return json.loads(manifest_data)
    except Exception as e:
        print(f"Warning: Failed to read manifest: {e}")
        return None


def extract_archive(archive_path, target_dir):
    """Extract archive contents to target directory."""
    print(f"Extracting archive to: {target_dir}")

    try:
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            # Get file list (excluding manifest)
            files = [f for f in zipf.namelist() if f != 'MANIFEST.json']

            # Extract files
            file_count = 0
            for file_path in files:
                zipf.extract(file_path, target_dir)
                file_count += 1
                if file_count % 100 == 0:
                    print(f"  Extracted {file_count}/{len(files)} files...", end='\r')

            print(f"  Extracted {file_count}/{len(files)} files... Done!")
            return file_count
    except Exception as e:
        print(f"Error: Failed to extract archive: {e}")
        sys.exit(1)


def run_command(cmd, cwd, description):
    """Run a shell command and handle errors."""
    print(f"\n>>> {description}")
    print(f"    Command: {' '.join(cmd)}")
    print(f"    Working directory: {cwd}")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )

        # Show output if there's any
        if result.stdout:
            print(result.stdout)

        print(f"✓ {description} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error during: {description}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def run_deployment_steps(target_dir):
    """Run post-extraction deployment steps."""
    print("\n" + "="*50)
    print("Running deployment steps...")
    print("="*50)

    backend_dir = target_dir / 'backend'
    frontend_dir = target_dir / 'frontend'

    steps = [
        {
            'cmd': ['pip', 'install', '-r', 'requirements.txt'],
            'cwd': backend_dir,
            'description': 'Installing backend dependencies'
        },
        {
            'cmd': ['alembic', 'upgrade', 'head'],
            'cwd': backend_dir,
            'description': 'Running database migrations'
        },
        {
            'cmd': ['npm', 'install'],
            'cwd': frontend_dir,
            'description': 'Installing frontend dependencies'
        },
        {
            'cmd': ['npm', 'run', 'build'],
            'cwd': frontend_dir,
            'description': 'Building frontend'
        }
    ]

    success_count = 0
    for step in steps:
        if run_command(step['cmd'], step['cwd'], step['description']):
            success_count += 1
        else:
            print("\n⚠ Deployment step failed. Please check the error above.")
            response = input("Continue with remaining steps? (y/n): ")
            if response.lower() != 'y':
                print("Deployment stopped by user")
                return False

    return success_count == len(steps)


def unpack_and_deploy():
    """Main unpacking and deployment function."""
    print("=== MailSeller Deployment Unpacker ===\n")

    # Determine archive path
    if len(sys.argv) > 1:
        archive_path = Path(sys.argv[1])
        if not archive_path.exists():
            print(f"Error: Archive not found: {archive_path}")
            sys.exit(1)
    else:
        # Auto-detect latest archive
        current_dir = Path.cwd()
        builds_dir = current_dir / 'builds'

        if not builds_dir.exists():
            print(f"Error: Builds directory not found: {builds_dir}")
            print("Usage: python unpack.py [path/to/archive.zip]")
            sys.exit(1)

        print("No archive specified, searching for latest...")
        archive_path = find_latest_archive(builds_dir)
        print(f"Found: {archive_path.name}")

    # Validate it's a zip file
    if not zipfile.is_zipfile(archive_path):
        print(f"Error: Not a valid zip file: {archive_path}")
        sys.exit(1)

    print(f"\nArchive: {archive_path.name}")

    # Extract and display manifest
    manifest = extract_manifest(archive_path)
    if manifest:
        print(f"\nManifest Information:")
        print(f"  Version:     {manifest.get('version', 'N/A')}")
        print(f"  Created:     {manifest.get('created_at', 'N/A')}")
        print(f"  Commit:      {manifest.get('commit', {}).get('hash', 'N/A')[:8]}")
        print(f"  Files:       {manifest.get('file_count', 'N/A')}")

    # Confirm extraction
    target_dir = Path.cwd()
    print(f"\nExtraction target: {target_dir}")
    print("⚠ Warning: This will overwrite existing files!")

    response = input("\nProceed with extraction and deployment? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled")
        sys.exit(0)

    # Extract archive
    print("\n" + "="*50)
    print("Extracting files...")
    print("="*50)
    file_count = extract_archive(archive_path, target_dir)

    # Run deployment steps
    deployment_success = run_deployment_steps(target_dir)

    # Final summary
    print("\n" + "="*50)
    if deployment_success:
        print("✓ Deployment completed successfully!")
    else:
        print("⚠ Deployment completed with errors")
    print("="*50)
    print(f"Version:     {manifest.get('version', 'N/A') if manifest else 'N/A'}")
    print(f"Files:       {file_count}")
    print(f"Location:    {target_dir}")
    print("="*50 + "\n")

    if not deployment_success:
        print("Please review the errors above and fix any issues.")
        sys.exit(1)


if __name__ == '__main__':
    try:
        unpack_and_deploy()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
