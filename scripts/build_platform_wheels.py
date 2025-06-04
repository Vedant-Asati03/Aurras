#!/usr/bin/env python3
"""
Platform-specific wheel builder for Aurras.
Creates separate wheels for Windows (with DLL) and other platforms (without DLL).
"""

import sys
import shutil
import platform
import subprocess
from pathlib import Path


def build_windows_wheel():
    """Build wheel with Windows DLL included."""
    print("🔨 Building Windows wheel (with libmpv-2.dll)...")

    # Ensure DLL is present
    dll_path = Path("aurras/core/player/libmpv-2.dll")
    if not dll_path.exists():
        print(f"❌ Error: {dll_path} not found!")
        return False
    # Backup original pyproject.toml
    pyproject_path = Path("pyproject.toml")

    with open(pyproject_path, "r") as f:
        original_content = f.read()

    # Create temporary pyproject.toml with DLL inclusion
    windows_config = (
        original_content
        + """
# Windows-specific DLL inclusion
[tool.hatch.build.targets.wheel.force-include]
"aurras/core/player/libmpv-2.dll" = "aurras/core/player/libmpv-2.dll"
"""
    )

    try:
        # Write modified config
        with open(pyproject_path, "w") as f:
            f.write(windows_config)
        # Build with uv
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
            print(f"📦 Renamed wheel to: {new_wheel_path.name}")

        print("✅ Windows wheel built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Windows wheel: {e}")
        return False
    finally:
        # Restore original pyproject.toml
        with open(pyproject_path, "w") as f:
            f.write(original_content)


def build_universal_wheel():
    """Build wheel without Windows DLL for Linux/macOS."""
    print("🔨 Building universal wheel (without libmpv-2.dll)...")

    dll_path = Path("aurras/core/player/libmpv-2.dll")
    temp_dll_path = None  # Temporarily move DLL if it exists
    if dll_path.exists():
        temp_dll_path = Path("libmpv-2.dll.tmp")
        shutil.move(str(dll_path), str(temp_dll_path))
        print(f"📦 Temporarily moved DLL to {temp_dll_path}")

    try:
        # Build without DLL using uv
        subprocess.run(["uv", "build", "--wheel"], check=True)

        # Rename the wheel to indicate it's universal (no Windows DLL)
        wheel_files = list(Path("dist").glob("*-py3-none-any.whl"))
        if wheel_files:
            original_wheel = wheel_files[-1]  # Get the most recent wheel
            # Change from py3-none-any to py3-none-linux_x86_64 (or keep as any)
            new_name = str(original_wheel).replace(
                "-py3-none-any.whl", "-py3-none-universal.whl"
            )
            new_wheel_path = Path(new_name)
            original_wheel.rename(new_wheel_path)
            print(f"📦 Renamed wheel to: {new_wheel_path.name}")

        print("✅ Universal wheel built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build universal wheel: {e}")
        return False
    finally:
        # Restore DLL if it was moved
        if temp_dll_path and temp_dll_path.exists():
            shutil.move(str(temp_dll_path), str(dll_path))
            print(f"📦 Restored DLL to {dll_path}")


def main():
    """Main build function."""
    print("🚀 Building platform-specific wheels for Aurras")
    print(f"📍 Platform: {platform.system()} ({platform.machine()})")

    # Create dist directory if it doesn't exist
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # Clean up any existing wheels for fresh build
    for wheel in dist_dir.glob("*.whl"):
        wheel.unlink()
        print(f"🗑️ Removed existing wheel: {wheel.name}")

    current_platform = platform.system().lower()

    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Build both versions (useful for CI)
        print("🏗️ Building all wheel variants...")
        success = True
        success &= build_windows_wheel()
        success &= build_universal_wheel()

        if success:
            print("🎉 All wheels built successfully!")
            print("📦 Windows wheel includes libmpv-2.dll (117MB)")
            print("📦 Universal wheel excludes libmpv-2.dll (smaller)")
        else:
            print("💥 Some builds failed!")
            sys.exit(1)

    elif current_platform == "windows":
        # On Windows, build the Windows-specific wheel
        if not build_windows_wheel():
            sys.exit(1)
    else:
        # On other platforms, build the universal wheel
        if not build_universal_wheel():
            sys.exit(1)

    print("\n🏁 Build complete!")
    print("ℹ️  To upload to PyPI:")
    print("   twine upload dist/*")


if __name__ == "__main__":
    main()
