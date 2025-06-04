#!/usr/bin/env python3
"""
Release management script for Aurras.
Synchronizes version numbers and metadata across all packaging files.
"""

import re
import sys
from pathlib import Path
from typing import List


def is_prerelease(version: str) -> bool:
    """Check if version is a pre-release (beta, rc, alpha)."""
    return any(tag in version.lower() for tag in ["a", "b", "rc", "alpha", "beta"])


def get_automation_level(version: str) -> str:
    """Determine what gets automated based on version type."""
    if is_prerelease(version):
        return "PyPI + GitHub only (pre-release)"
    else:
        return "All package managers (stable release)"


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    else:
        raise ValueError("Could not find version in pyproject.toml")


def update_version_in_file(
    file_path: Path, old_version: str, new_version: str, patterns: List[str]
) -> bool:
    """Update version in a specific file using provided patterns."""
    if not file_path.exists():
        print(f"⚠️  {file_path} not found, skipping...")
        return False

    content = file_path.read_text()
    updated = False

    for pattern in patterns:
        old_pattern = pattern.format(version=old_version)
        new_pattern = pattern.format(version=new_version)

        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            updated = True

    if updated:
        file_path.write_text(content)
        print(f"✅ Updated {file_path}")
        return True
    else:
        print(f"🔍 No version patterns found in {file_path}")
        return False


def update_all_versions(new_version: str) -> None:
    """Update version across all packaging files."""
    current_version = get_current_version()

    if current_version == new_version:
        print(f"🎯 Version is already {new_version}")
        return

    print(f"🚀 Updating version: {current_version} → {new_version}")
    print()

    # Define version patterns for each file type
    version_updates = {
        "pyproject.toml": ['version = "{version}"'],
        "packaging/choco/aurras.nuspec": ["<version>{version}</version>"],
        "packaging/homebrew/aurras.rb": [
            'url "https://files.pythonhosted.org/packages/source/a/aurras/aurras-{version}.tar.gz"'
        ],
        "packaging/aur/PKGBUILD": [
            "pkgver={version}",
            'source=("https://files.pythonhosted.org/packages/source/a/aurras/aurras-${{pkgver}}.tar.gz")',
        ],
    }

    updated_files = []
    for file_path, patterns in version_updates.items():
        if update_version_in_file(
            Path(file_path), current_version, new_version, patterns
        ):
            updated_files.append(file_path)

    print()
    print("📋 Summary:")
    print(f"   Updated {len(updated_files)} files")
    for file_path in updated_files:
        print(f"   ✅ {file_path}")

    print()
    print("🎯 Next steps:")
    automation_level = get_automation_level(new_version)
    print(f"   🤖 Automation: {automation_level}")
    print("   1. Review changes with: git diff")
    print("   2. Test builds locally")
    print(
        "   3. Commit changes: git add . && git commit -m 'Bump version to v{}'".format(
            new_version
        )
    )
    print(
        "   4. Create release tag: git tag v{} && git push origin v{}".format(
            new_version, new_version
        )
    )
    print()
    if is_prerelease(new_version):
        print("📝 Pre-release notes:")
        print("   • PyPI will mark as pre-release")
        print("   • GitHub will mark as pre-release")
        print("   • Other package managers will be skipped")
        print("   • Users need: pip install aurras=={}".format(new_version))
    else:
        print("🚀 Stable release notes:")
        print("   • All package managers will be updated automatically")
        print("   • Chocolatey: ~30-60 min moderation delay")
        print("   • Homebrew: PR created (manual approval needed)")
        print("   • AUR: Updated immediately (if SSH key configured)")
        print("   • Monitor: GitHub Actions for build status")


def check_sync_status() -> None:
    """Check if all packaging files are in sync."""
    current_version = get_current_version()
    print(f"🔍 Checking sync status for version {current_version}")
    print()

    # Check each file for version consistency
    files_to_check = {
        "packaging/choco/aurras.nuspec": [f"<version>{current_version}</version>"],
        "packaging/homebrew/aurras.rb": [f"aurras-{current_version}.tar.gz"],
        "packaging/aur/PKGBUILD": [f"pkgver={current_version}"],
    }

    all_synced = True
    for file_path, patterns in files_to_check.items():
        file = Path(file_path)
        if file.exists():
            content = file.read_text()
            synced = all(pattern in content for pattern in patterns)
            status = "✅" if synced else "❌"
            print(f"   {status} {file_path}")
            if not synced:
                all_synced = False
        else:
            print(f"   ⚠️  {file_path} (missing)")
            all_synced = False

    print()
    if all_synced:
        print("🎉 All files are in sync!")
    else:
        print("⚠️  Some files are out of sync. Run with version number to update.")


def main():
    """Main function."""
    if len(sys.argv) == 1:
        # No arguments - check sync status
        check_sync_status()
    elif len(sys.argv) == 2:
        # Version argument provided - update all files
        new_version = sys.argv[1]
        if new_version.startswith("v"):
            new_version = new_version[1:]  # Remove 'v' prefix
        update_all_versions(new_version)
    else:
        print("Usage:")
        print("  python scripts/release_manager.py           # Check sync status")
        print("  python scripts/release_manager.py 1.2.0     # Update to version 1.2.0")
        print("  python scripts/release_manager.py v1.2.0    # Update to version 1.2.0")


if __name__ == "__main__":
    main()
