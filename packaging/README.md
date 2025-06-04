# Aurras Packaging

This directory contains packaging files for distributing Aurras across different package managers and platforms.

## Supported Package Managers

### 🐍 PyPI (Primary)
- **Installation**: `pip install aurras`
- **Automation**: Fully automated via GitHub Actions
- **Platforms**: Windows (with bundled MPV), Linux, macOS
- **Status**: ✅ Active with automated publishing

### 🪟 Chocolatey (Windows)
- **Installation**: `choco install aurras`
- **Files**: `choco/aurras.nuspec`, `choco/tools/`
- **Dependencies**: Python 3.12+
- **Status**: 🚧 Ready for submission

### 🍎 Homebrew (macOS)
- **Installation**: `brew install aurras`
- **Files**: `homebrew/aurras.rb`
- **Dependencies**: Python 3.12+, MPV
- **Status**: 🚧 Ready for submission

### 🐧 AUR (Arch Linux)
- **Installation**: `yay -S aurras` or `paru -S aurras`
- **Files**: `aur/PKGBUILD`
- **Dependencies**: Python 3.12+, MPV
- **Status**: 🚧 Ready for submission

## Complete Release Management Workflow

### 🛠️ Development Phase
1. **Work on features** in feature branches
2. **Test changes** locally with `python -m aurras`
3. **Merge to main** when ready for release

### 📋 Pre-Release Preparation
1. **Check current sync status**:
   ```bash
   python scripts/release_manager.py
   ```

2. **Update version everywhere** (if needed):
   ```bash
   python scripts/release_manager.py 1.2.0
   ```

3. **Review changes**:
   ```bash
   git diff
   ```

4. **Test builds locally**:
   ```bash
   # Test Windows wheel (on Windows)
   python scripts/build_platform_wheels.py windows
   
   # Test universal wheel
   python scripts/build_platform_wheels.py universal
   
   # Test both
   python scripts/build_platform_wheels.py --all
   ```

### 🚀 Release Process
1. **Commit version updates**:
   ```bash
   git add .
   git commit -m "Bump version to v1.2.0"
   ```

2. **Create and push release tag**:
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```

3. **Automated PyPI release**:
   - GitHub Actions triggers on `v*` tags
   - Builds Windows wheel (with MPV DLL) and universal wheel
   - Publishes both wheels to PyPI
   - Creates GitHub Release with downloadable files

### 📦 Manual Package Manager Updates

#### Chocolatey (Windows)
1. **Verify package**:
   ```powershell
   choco pack packaging/choco/aurras.nuspec
   ```

2. **Submit to Chocolatey**:
   - Upload `.nupkg` to [Chocolatey Community Repository](https://community.chocolatey.org/packages/upload)
   - Wait for automatic moderation approval
   - Package becomes available via `choco install aurras`

#### Homebrew (macOS)
1. **Calculate SHA256** of source tarball:
   ```bash
   curl -sL https://files.pythonhosted.org/packages/source/a/aurras/aurras-1.2.0.tar.gz | shasum -a 256
   ```

2. **Update formula** with new SHA256 in `homebrew/aurras.rb`

3. **Submit pull request** to [homebrew-core](https://github.com/Homebrew/homebrew-core)

#### AUR (Arch Linux)
1. **Update PKGBUILD**:
   ```bash
   cd packaging/aur
   makepkg --printsrcinfo > .SRCINFO
   ```

2. **Submit to AUR**:
   ```bash
   git clone ssh://aur@aur.archlinux.org/aurras.git
   cp PKGBUILD .SRCINFO aurras/
   cd aurras
   git add . && git commit -m "Update to 1.2.0"
   git push
   ```

### ⚡ Quick Release Commands
```bash
# Check if everything is in sync
python scripts/release_manager.py

# Update version and create release
python scripts/release_manager.py 1.2.0
git add . && git commit -m "Bump version to v1.2.0"
git tag v1.2.0 && git push origin v1.2.0

# PyPI happens automatically via GitHub Actions
# Manual package managers require individual submission
```

## Package Manager Coverage

| Platform | Package Manager | Status  | Coverage    |
| -------- | --------------- | ------- | ----------- |
| Windows  | PyPI            | ✅ Live  | All users   |
| Windows  | Chocolatey      | 🚧 Ready | Power users |
| macOS    | PyPI            | ✅ Live  | All users   |
| macOS    | Homebrew        | 🚧 Ready | Most users  |
| Linux    | PyPI            | ✅ Live  | All users   |
| Linux    | AUR             | 🚧 Ready | Arch users  |

## Dependencies by Platform

- **Windows**: Self-contained (bundled MPV DLL)
- **macOS**: Requires `brew install mpv`
- **Linux**: Requires system MPV (`apt install mpv`, `pacman -S mpv`, etc.)

## Maintenance

Package files should be updated when:
- Version changes in `pyproject.toml`
- Dependencies change
- New features require platform-specific handling
- Security updates for packaging systems
