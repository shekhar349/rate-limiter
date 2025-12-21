# Publishing Guide

This guide explains how to publish the python-rate-limiter package to PyPI.

## Prerequisites

1. **Check Package Name Availability**
   - The name `python-rate-limiter` might already be taken on PyPI
   - Check availability: https://pypi.org/project/python-rate-limiter/
   - If taken, consider alternatives like:
     - `api-rate-limiter`
     - `fastapi-flask-django-rate-limiter`
     - Or use your own namespace: `yourname-rate-limiter`

2. **Create PyPI Accounts**
   - [PyPI](https://pypi.org/account/register/) - for production releases
   - [TestPyPI](https://test.pypi.org/account/register/) - for testing releases

3. **Update setup.py**
   - Update `author` and `author_email` with your information
   - Update `url` with your actual repository URL
   - If name is taken, update `name` field

## Publishing Steps

### 1. Install Build Tools

```bash
pip install build twine
```

### 2. Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source and wheel distributions
python -m build
```

This creates:
- `dist/python-rate-limiter-0.1.0.tar.gz` (source distribution)
- `dist/python_rate_limiter-0.1.0-py3-none-any.whl` (wheel distribution)

### 3. Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ python-rate-limiter
```

### 4. Publish to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*
```

You'll be prompted for your PyPI username and password.

### 5. Verify Installation

```bash
# Create a new virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from PyPI
pip install python-rate-limiter

# Test import
python -c "from python_rate_limiter import RateLimiter; print('Success!')"
```

## Updating the Package

1. **Update Version**
   - Update `version` in `setup.py`
   - Follow [Semantic Versioning](https://semver.org/):
     - `MAJOR.MINOR.PATCH` (e.g., 0.1.0 → 0.1.1 for bug fixes)

2. **Update CHANGELOG** (if you have one)
   - Document changes in the new version

3. **Rebuild and Upload**
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Security: Using API Tokens

Instead of passwords, use API tokens:

1. Go to PyPI Account Settings → API tokens
2. Create a new token
3. Use it with twine:
   ```bash
   python -m twine upload --username __token__ --password pypi-<your-token> dist/*
   ```

## Alternative: GitHub Actions

You can automate publishing with GitHub Actions. Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## Notes

- The package name uses hyphens (`python-rate-limiter`) and the Python module uses underscores (`python_rate_limiter`)
- This is standard Python packaging convention
- Users install with `pip install python-rate-limiter` and import with `from python_rate_limiter import ...`

