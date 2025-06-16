#!/usr/bin/env python3
"""
Generate .SRCINFO file from PKGBUILD for AUR packages.
This script replaces the need for makepkg --printsrcinfo on non-Arch systems.
"""

import re
import sys
from pathlib import Path


def extract_field(content: str, field: str, is_array: bool = False) -> str | list:
    """Extract a field from PKGBUILD content."""
    if is_array:
        # Handle array fields like depends=('dep1' 'dep2')
        pattern = rf"{field}=\(([^)]+)\)"
        match = re.search(pattern, content)
        if match:
            # Split and clean up array elements
            elements = match.group(1).replace("\n", " ").split()
            return [elem.strip().strip("'\"") for elem in elements if elem.strip()]
        return []
    else:
        # Handle simple fields like pkgname=value or pkgname="value"
        pattern = rf'{field}=(["\']?)([^"\'\s]+)\1'
        match = re.search(pattern, content)
        if match:
            return match.group(2)
        return ""


def generate_srcinfo(pkgbuild_path: Path) -> str:
    """Generate .SRCINFO content from PKGBUILD."""
    if not pkgbuild_path.exists():
        raise FileNotFoundError(f"PKGBUILD not found: {pkgbuild_path}")

    content = pkgbuild_path.read_text()

    # Extract basic fields
    pkgname = extract_field(content, "pkgname")
    pkgver = extract_field(content, "pkgver")
    pkgrel = extract_field(content, "pkgrel")
    pkgdesc = extract_field(content, "pkgdesc")
    arch = extract_field(content, "arch", is_array=True)
    url = extract_field(content, "url")
    license = extract_field(content, "license", is_array=True)

    # Extract dependency arrays
    depends = extract_field(content, "depends", is_array=True)
    makedepends = extract_field(content, "makedepends", is_array=True)
    source = extract_field(content, "source", is_array=True)
    sha256sums = extract_field(content, "sha256sums", is_array=True)

    # Build .SRCINFO content
    lines = [
        f"pkgbase = {pkgname}",
        f"\tpkgdesc = {pkgdesc}",
        f"\tpkgver = {pkgver}",
        f"\tpkgrel = {pkgrel}",
        f"\turl = {url}",
    ]

    # Add architecture
    for a in arch:
        lines.append(f"\tarch = {a}")

    # Add licenses
    for lic in license:
        lines.append(f"\tlicense = {lic}")

    # Add dependencies
    for dep in depends:
        lines.append(f"\tdepends = {dep}")

    for makedep in makedepends:
        lines.append(f"\tmakedepends = {makedep}")

    # Add sources
    for src in source:
        lines.append(f"\tsource = {src}")

    # Add checksums
    for sha in sha256sums:
        lines.append(f"\tsha256sums = {sha}")

    # Add package section
    lines.extend(["", f"pkgname = {pkgname}"])

    return "\n".join(lines) + "\n"


def main():
    """Main function."""
    pkgbuild_path = Path("PKGBUILD")

    if len(sys.argv) > 1:
        pkgbuild_path = Path(sys.argv[1])

    try:
        srcinfo_content = generate_srcinfo(pkgbuild_path)

        # Write to .SRCINFO
        srcinfo_path = pkgbuild_path.parent / ".SRCINFO"
        srcinfo_path.write_text(srcinfo_content)

        print(f"Generated {srcinfo_path} successfully")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
