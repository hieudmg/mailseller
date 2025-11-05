#!/usr/bin/env python3
"""
Pack script for air-gapped deployment.
Creates a zip archive of all git-tracked files with timestamp-based versioning.
"""

import subprocess
import zipfile
import json
from pathlib import Path
from datetime import datetime
import sys


def get_git_root():
    """Get the root directory of the git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository")
        sys.exit(1)


def get_git_commit_info():
    """Get current git commit information."""
    try:
        commit_hash = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()

        commit_message = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        commit_author = subprocess.run(
            ["git", "log", "-1", "--pretty=%an"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        commit_date = subprocess.run(
            ["git", "log", "-1", "--pretty=%ai"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        return {
            "hash": commit_hash,
            "message": commit_message,
            "author": commit_author,
            "date": commit_date,
        }
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get git commit info: {e}")
        sys.exit(1)


def get_tracked_files():
    """Get list of all git-tracked files."""
    try:
        result = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, check=True
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get tracked files: {e}")
        sys.exit(1)


def create_manifest(version, commit_info, file_count):
    """Create manifest data."""
    return {
        "version": version,
        "commit": commit_info,
        "created_at": datetime.now().isoformat(),
        "file_count": file_count,
    }


def pack_files():
    """Main packing function."""
    print("=== MailSeller Deployment Packer ===\n")

    # Get git root and change to it
    git_root = get_git_root()
    print(f"Git repository root: {git_root}")

    # Get commit info
    print("Gathering commit information...")
    commit_info = get_git_commit_info()
    print(f"Current commit: {commit_info['hash'][:8]}")
    print(f"Commit message: {commit_info['message'][:60]}...")

    # Generate version
    version = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"\nVersion: {version}")

    # Get tracked files
    print("\nGathering git-tracked files...")
    tracked_files = get_tracked_files()
    print(f"Found {len(tracked_files)} tracked files")

    # Create builds directory
    builds_dir = git_root / "builds"
    builds_dir.mkdir(exist_ok=True)

    # Create archive name
    archive_name = f"mailseller-{version}.zip"
    archive_path = builds_dir / archive_name

    print(f"\nCreating archive: {archive_name}")

    # Create manifest
    manifest = create_manifest(version, commit_info, len(tracked_files))

    # Create zip archive
    try:
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add manifest
            zipf.writestr("MANIFEST.json", json.dumps(manifest, indent=2))

            # Add all tracked files
            file_count = 0
            for file_path in tracked_files:
                full_path = git_root / file_path
                if full_path.exists():
                    zipf.write(full_path, file_path)
                    file_count += 1
                    if file_count % 100 == 0:
                        print(
                            f"  Packed {file_count}/{len(tracked_files)} files...",
                            end="\r",
                        )

            print(f"  Packed {file_count}/{len(tracked_files)} files... Done!")

        # Get archive size
        archive_size = archive_path.stat().st_size
        size_mb = archive_size / (1024 * 1024)

        print(f"\n{'='*50}")
        print("✓ Archive created successfully!")
        print(f"{'='*50}")
        print(f"Location:    {archive_path}")
        print(f"Version:     {version}")
        print(f"Files:       {file_count}")
        print(f"Size:        {size_mb:.2f} MB")
        print(f"Commit:      {commit_info['hash'][:8]}")
        print(f"{'='*50}\n")

    except Exception as e:
        print(f"\nError: Failed to create archive: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        pack_files()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
