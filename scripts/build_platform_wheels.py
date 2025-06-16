#!/usr/bin/env python3
"""
Platform-specific wheel builder for Aurras.
Creates separate wheels for Windows (with DLL) and other platforms (without DLL).
"""

import sys
import platform
import subprocess
from pathlib import Path


def build_windows_wheel():
    """Build wheel with Windows DLL included."""
    print("Building Windows wheel (with libmpv-2.dll)...")

    # Ensure DLL is present
    dll_path = Path("aurras/core/player/libmpv-2.dll")
    if not dll_path.exists():
        print(f"Error: {dll_path} not found!")
        return False

    # Backup original pyproject.toml
    pyproject_path = Path("pyproject.toml")

    with open(pyproject_path, "r") as f:
        original_content = f.read()

    # Temporarily add package-data configuration for Windows DLL
    modified_content = original_content.replace(
        'exclude = ["assets*", "packaging*", "docs*", "tests*", "scripts*"]',
        'exclude = ["assets*", "packaging*", "docs*", "tests*", "scripts*"]\n\n[tool.setuptools.package-data]\n"aurras.core.player" = ["*.dll"]',
    )

    # Write the modified pyproject.toml
    with open(pyproject_path, "w") as f:
        f.write(modified_content)
    print("Temporarily added DLL package-data to pyproject.toml")

    try:
        # Build with uv (DLL will be included due to package-data config)
        subprocess.run(["uv", "build", "--wheel"], check=True)

        # Rename the wheel to indicate it's Windows-specific
        wheel_files = list(Path("dist").glob("*.whl"))
        if wheel_files:
            original_wheel = wheel_files[-1]  # Get the most recent wheel
            # Change from py3-none-any to py3-none-win_amd64
            new_name = str(original_wheel).replace(
                "-py3-none-any.whl", "-py3-none-win_amd64.whl"
            )
            new_wheel_path = Path(new_name)
            original_wheel.rename(new_wheel_path)
            print(f"Renamed wheel to: {new_wheel_path.name}")

        print("Windows wheel built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to build Windows wheel: {e}")
        return False
    finally:
        # Restore original pyproject.toml
        with open(pyproject_path, "w") as f:
            f.write(original_content)
        print("Restored original pyproject.toml")


def build_universal_wheel():
    """Build wheel without Windows DLL for Linux/macOS."""
    print("Building universal wheel (without libmpv-2.dll)...")

    # Temporarily move the DLL file so it's not included in the wheel
    dll_path = Path("aurras/core/player/libmpv-2.dll")
    temp_dll_path = Path("libmpv-2.dll.tmp")

    dll_moved = False
    if dll_path.exists():
        dll_path.rename(temp_dll_path)
        dll_moved = True
        print(f"Temporarily moved DLL to {temp_dll_path}")

    # Also need to clean any existing build directories to avoid cached files
    build_dirs = ["build", "aurras.egg-info"]
    for build_dir in build_dirs:
        if Path(build_dir).exists():
            import shutil

            shutil.rmtree(build_dir)
            print(f"Cleaned {build_dir} directory")

    try:
        # Build without DLL using uv
        subprocess.run(["uv", "build", "--wheel"], check=True)

        # Rename the wheel to indicate it's universal (no Windows DLL)
        wheel_files = list(Path("dist").glob("*-py3-none-any.whl"))
        if wheel_files:
            print(f"Universal wheel built: {wheel_files[-1].name}")

        print("Universal wheel built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to build universal wheel: {e}")
        return False
    finally:
        # Restore the DLL
        if dll_moved and temp_dll_path.exists():
            temp_dll_path.rename(dll_path)
            print(f"Restored DLL to {dll_path}")


def main():
    """Main build function."""
    print("Building platform-specific wheels for Aurras")
    print(f"Platform: {platform.system()} ({platform.machine()})")

    # Create dist directory if it doesn't exist
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # Clean up any existing wheels for fresh build
    for wheel in dist_dir.glob("*.whl"):
        wheel.unlink()
        print(f"Removed existing wheel: {wheel.name}")

    current_platform = platform.system().lower()

    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Build both versions (useful for CI)
        print("Building all wheel variants...")
        success = True
        success &= build_windows_wheel()
        success &= build_universal_wheel()

        if success:
            print("All wheels built successfully!")
            print("Windows wheel includes libmpv-2.dll (117MB)")
            print("Universal wheel excludes libmpv-2.dll (smaller)")
        else:
            print("Some builds failed!")
            sys.exit(1)

    elif current_platform == "windows":
        # On Windows, build the Windows-specific wheel
        if not build_windows_wheel():
            sys.exit(1)
    else:
        # On other platforms, build the universal wheel
        if not build_universal_wheel():
            sys.exit(1)

    print("\nBuild complete!")
    print("To upload to PyPI:")
    print("   twine upload dist/*")


if __name__ == "__main__":
    main()
