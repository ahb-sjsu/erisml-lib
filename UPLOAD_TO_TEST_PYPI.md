# Uploading to Test PyPI

## Option 1: Using Environment Variables (Recommended)

Run these commands in your terminal:

```bash
# Set your test PyPI credentials
export TWINE_USERNAME=__token__  # Use __token__ if using API token
export TWINE_PASSWORD=your_test_pypi_api_token_here

# Upload to test PyPI
cd /Users/kunalsahni/Desktop/erisml-lib
python -m twine upload --repository testpypi dist/*
```

**Note:** For test PyPI, you can use:
- Username: `__token__` and password: your API token (recommended)
- OR your test PyPI username and password

## Option 2: Using .pypirc file

Create a file `~/.pypirc` with:

```ini
[distutils]
index-servers =
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = your_test_pypi_api_token_here
```

Then run:
```bash
python -m twine upload --repository testpypi dist/*
```

## Option 3: Direct command with credentials

```bash
python -m twine upload --repository testpypi \
  --username __token__ \
  --password your_test_pypi_api_token_here \
  dist/*
```

## Getting Test PyPI API Token

1. Go to https://test.pypi.org/manage/account/
2. Scroll to "API tokens"
3. Create a new token (scope: "Entire account" or project-specific)
4. Copy the token (starts with `pypi-`)

## After Upload

Test the installation:

```bash
# Create a clean virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ erisml

# Verify installation
erisml-mcp-server --help
python -c "from erisml import __version__; print(f'Version: {__version__.__version__}')"
python -c "from erisml.ethics import EthicalFacts, EthicalJudgement; print('OK - Ethics module imports work')"
```

