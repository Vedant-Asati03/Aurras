# Contributing to Aurras

Thank you for considering contributing to Aurras! This document outlines the process for contributing to the project and the standards we follow.

## Table of Contents
- [Contributing to Aurras](#contributing-to-aurras)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [Getting Started](#getting-started)
  - [Development Environment](#development-environment)
  - [Coding Standards](#coding-standards)
  - [Testing](#testing)
  - [Pull Request Process](#pull-request-process)
  - [Branch Naming Convention](#branch-naming-convention)
  - [Versioning](#versioning)

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/vedant-asati03/Aurras.git`
3. Set up the development environment as described below
4. Create a branch for your changes

## Development Environment

1. Install Python 3.12 or higher
2. Install external dependencies (MPV, FFmpeg) as described in the README
3. Install the package in development mode:
   ```
   cd Aurras
   pip install -e .
   ```
4. Install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

## Coding Standards

We follow these coding standards:

- Code formatting with [Black](https://black.readthedocs.io/en/stable/)
- Import sorting with [isort](https://pycqa.github.io/isort/)
- Linting with [Flake8](https://flake8.pycqa.org/en/latest/)
- Type checking with [Mypy](https://mypy.readthedocs.io/)
- Docstrings using Google style format

Before submitting changes, please run:

```bash
# Format code
black .
isort .

# Check for issues
flake8
mypy .
```

## Testing

Write tests for new features and ensure all tests pass before submitting pull requests:

```bash
pytest
```

For coverage reports:

```bash
pytest --cov=aurras
```

## Pull Request Process

1. Update the README.md and documentation with details of changes
2. Update the CHANGELOG.md with notes on your changes
3. Make sure all tests pass and code quality checks are satisfied
4. The PR should be reviewed by at least one maintainer
5. Once approved, a maintainer will merge your PR

## Branch Naming Convention

- `feature/my-new-feature`: For new features
- `bugfix/issue-description`: For bug fixes
- `docs/what-is-changing`: For documentation updates
- `refactor/what-is-changing`: For code refactoring

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/USERNAME/Aurras/tags).
