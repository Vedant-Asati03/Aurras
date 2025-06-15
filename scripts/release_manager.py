#!/usr/bin/env python3
"""
Release management script for Aurras.
Synchronizes version numbers and metadata across all packaging files.
Updated: June 2025 - Enhanced with better validation and error handling.
"""

import re
import sys
import hashlib
import urllib.request
from pathlib import Path
from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def validate_semantic_version(version: str) -> bool:
    """Validate if version follows semantic versioning (semver) format."""
    # Regex pattern for semantic versioning (basic)
    # Supports: X.Y.Z, X.Y.Z-alpha.N, X.Y.Z-beta.N, X.Y.Z-rc.N
    pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(alpha|beta|rc)(?:\.(0|[1-9]\d*))?)?$"

    if not re.match(pattern, version):
        logger.error(f"Invalid version format: {version}")
        logger.error("   Expected format: X.Y.Z or X.Y.Z-prerelease")
        logger.error("   Examples: 1.2.3, 1.0.0-alpha.1, 2.1.0-beta, 1.5.0-rc.2")
        return False

    return True


def safe_file_operation(operation_name: str, file_path: Path, operation_func):
    """Safely perform file operations with error handling."""
    try:
        return operation_func()
    except FileNotFoundError:
        logger.error(f"ERROR {operation_name} failed: {file_path} not found")
        return False
    except PermissionError:
        logger.error(f"ERROR {operation_name} failed: Permission denied for {file_path}")
        return False
    except Exception as e:
        logger.error(f"ERROR {operation_name} failed: {e}")
        return False


def fetch_pypi_sha256(package_name: str, version: str) -> str:
    """Fetch SHA256 hash for a package version from PyPI with enhanced error handling."""
    try:
        url = f"https://files.pythonhosted.org/packages/source/{package_name[0]}/{package_name}/{package_name}-{version}.tar.gz"
        logger.info(f"FETCH Fetching SHA256 for {package_name} v{version}...")

        request = urllib.request.Request(url)
        request.add_header("User-Agent", "Aurras-Release-Manager/2.0")

        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise urllib.error.HTTPError(
                    url, response.status, f"HTTP {response.status}", {}, None
                )

            content = response.read()
            sha256_hash = hashlib.sha256(content).hexdigest()
            logger.info(f"SUCCESS SHA256: {sha256_hash}")
            return sha256_hash

    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.warning(f"WARNING  Package version {version} not found on PyPI yet")
            logger.info(
                "   This is expected for new releases - package will be uploaded later"
            )
        else:
            logger.error(f"WARNING  HTTP error {e.code}: {e.reason}")
        return "SKIP"
    except urllib.error.URLError as e:
        logger.error(f"WARNING  Network error: {e.reason}")
        return "SKIP"
    except Exception as e:
        logger.error(f"WARNING  Unexpected error fetching SHA256: {e}")
        logger.info("   Using 'SKIP' placeholder - manual update needed")
        return "SKIP"


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
        print(f"WARNING  {file_path} not found, skipping...")
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
        print(f"SUCCESS Updated {file_path}")
        return True
    else:
        print(f"SEARCH No version patterns found in {file_path}")
        return False


def update_all_versions(new_version: str) -> None:
    """Update version across all packaging files with enhanced validation."""
    # Validate version format first
    if not validate_semantic_version(new_version):
        logger.error("ERROR Version update aborted due to invalid format")
        sys.exit(1)

    current_version = get_current_version()

    if current_version == new_version:
        logger.info(f"TARGET Version is already {new_version}")
        return

    logger.info(f"START Updating version: {current_version} -> {new_version}")
    logger.info("")

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
    failed_files = []

    for file_path, patterns in version_updates.items():

        def update_operation():
            return update_version_in_file(
                Path(file_path), current_version, new_version, patterns
            )

        result = safe_file_operation(
            f"Updating {file_path}", Path(file_path), update_operation
        )
        if result:
            updated_files.append(file_path)
        else:
            failed_files.append(file_path)

    # Special handling for AUR SHA256 update
    aur_pkgbuild = Path("packaging/aur/PKGBUILD")
    if aur_pkgbuild.exists():
        print("SECURE Updating AUR SHA256 hash...")
        sha256_hash = fetch_pypi_sha256("aurras", new_version)

        if sha256_hash != "SKIP":
            content = aur_pkgbuild.read_text()
            # Update SHA256 - match any existing hash pattern
            sha256_pattern = r"sha256sums=\('[^']+'\)"
            new_sha256 = f"sha256sums=('{sha256_hash}')"

            if re.search(sha256_pattern, content):
                content = re.sub(sha256_pattern, new_sha256, content)
                aur_pkgbuild.write_text(content)
                logger.info("SUCCESS Updated AUR SHA256 hash")
            else:
                logger.warning("WARNING  Could not find SHA256 pattern in PKGBUILD")

    # Special handling for Homebrew SHA256 update
    homebrew_formula = Path("packaging/homebrew/aurras.rb")
    if homebrew_formula.exists():
        print("BREW Updating Homebrew SHA256 hash...")
        sha256_hash = fetch_pypi_sha256("aurras", new_version)

        if sha256_hash != "SKIP":
            content = homebrew_formula.read_text()
            # Update SHA256 - match the placeholder pattern
            sha256_pattern = r'sha256 "PLACEHOLDER_SHA256_HASH"'
            new_sha256 = f'sha256 "{sha256_hash}"'

            if sha256_pattern in content:
                content = content.replace(sha256_pattern, new_sha256)
                homebrew_formula.write_text(content)
                logger.info("SUCCESS Updated Homebrew SHA256 hash")
            else:
                logger.warning(
                    "WARNING  Could not find SHA256 placeholder in Homebrew formula"
                )

    logger.info("")
    logger.info("SUMMARY Summary:")
    logger.info(f"   Updated {len(updated_files)} files successfully")
    for file_path in updated_files:
        logger.info(f"   SUCCESS {file_path}")

    if failed_files:
        logger.warning(f"   Failed to update {len(failed_files)} files:")
        for file_path in failed_files:
            logger.warning(f"   ERROR {file_path}")

    logger.info("")
    logger.info("TARGET Next steps:")
    automation_level = get_automation_level(new_version)
    logger.info(f"   AUTO Automation: {automation_level}")
    logger.info("   1. Review changes with: git diff")
    logger.info("   2. Test builds locally")
    logger.info(
        f"   3. Commit changes: git add . && git commit -m 'Bump version to v{new_version}'"
    )
    logger.info(
        f"   4. Create release tag: git tag v{new_version} && git push origin v{new_version}"
    )
    logger.info("")

    if is_prerelease(new_version):
        logger.info("NOTES Pre-release notes:")
        logger.info("   - PyPI will mark as pre-release")
        logger.info("   - GitHub will mark as pre-release")
        logger.info("   - Other package managers will be skipped")
        logger.info(f"   - Users need: pip install aurras=={new_version}")
    else:
        logger.info("START Stable release notes:")
        logger.info("   - All package managers will be updated automatically")
        logger.info("   - Chocolatey: ~30-60 min moderation delay")
        logger.info("   - Homebrew: PR created (manual approval needed)")
        logger.info("   - AUR: Updated immediately (if SSH key configured)")
        logger.info("   - Monitor: GitHub Actions for build status")

    if failed_files:
        logger.error("")
        logger.error("WARNING  Some files failed to update. Please review and fix manually.")
        sys.exit(1)


def check_sync_status() -> None:
    """Check if all packaging files are in sync with enhanced reporting."""
    current_version = get_current_version()
    logger.info(f"SEARCH Checking sync status for version {current_version}")
    logger.info("")

    # Check each file for version consistency
    files_to_check = {
        "packaging/choco/aurras.nuspec": [f"<version>{current_version}</version>"],
        "packaging/homebrew/aurras.rb": [f"aurras-{current_version}.tar.gz"],
        "packaging/aur/PKGBUILD": [f"pkgver={current_version}"],
    }

    all_synced = True
    missing_files = []
    out_of_sync_files = []

    for file_path, patterns in files_to_check.items():
        file = Path(file_path)
        if file.exists():
            content = file.read_text()
            synced = all(pattern in content for pattern in patterns)
            status = "SUCCESS" if synced else "ERROR"
            logger.info(f"   {status} {file_path}")
            if not synced:
                all_synced = False
                out_of_sync_files.append(file_path)
        else:
            logger.warning(f"   WARNING  {file_path} (missing)")
            all_synced = False
            missing_files.append(file_path)

    # Check for placeholder SHA256 hashes
    logger.info("")
    logger.info("SECURE SHA256 Hash Status:")

    # Check AUR SHA256
    aur_file = Path("packaging/aur/PKGBUILD")
    if aur_file.exists():
        content = aur_file.read_text()
        if "sha256sums=('SKIP')" in content:
            logger.warning("   WARNING  AUR: Using SKIP placeholder")
            all_synced = False
        else:
            logger.info("   SUCCESS AUR: Has SHA256 hash")

    # Check Homebrew SHA256
    homebrew_file = Path("packaging/homebrew/aurras.rb")
    if homebrew_file.exists():
        content = homebrew_file.read_text()
        if "PLACEHOLDER_SHA256_HASH" in content:
            logger.warning("   WARNING  Homebrew: Using placeholder SHA256")
            all_synced = False
        else:
            logger.info("   SUCCESS Homebrew: Has SHA256 hash")

    logger.info("")
    if all_synced:
        logger.info("COMPLETE All files are in sync!")
    else:
        logger.warning("WARNING  Some files are out of sync.")
        if missing_files:
            logger.error(f"   Missing files: {', '.join(missing_files)}")
        if out_of_sync_files:
            logger.error(f"   Out of sync: {', '.join(out_of_sync_files)}")
        logger.info("   Run with version number to update all files.")


def main():
    """Main function with enhanced argument handling."""
    if len(sys.argv) == 1:
        # No arguments - check sync status
        check_sync_status()
    elif len(sys.argv) == 2:
        # Version argument provided - update all files
        new_version = sys.argv[1]
        if new_version.startswith("v"):
            new_version = new_version[1:]  # Remove 'v' prefix

        logger.info(f"TARGET Starting version update to {new_version}")
        update_all_versions(new_version)
    else:
        logger.error("ERROR Invalid arguments")
        logger.info("")
        logger.info("Usage:")
        logger.info("  python scripts/release_manager.py           # Check sync status")
        logger.info(
            "  python scripts/release_manager.py 2.0.0     # Update to version 2.0.0"
        )
        logger.info(
            "  python scripts/release_manager.py v2.0.0    # Update to version 2.0.0"
        )
        logger.info("")
        logger.info("Supported version formats:")
        logger.info("  - Stable: 1.2.3, 2.0.0")
        logger.info("  - Pre-release: 1.2.3-alpha.1, 2.0.0-beta, 1.5.0-rc.2")
        sys.exit(1)


if __name__ == "__main__":
    main()
