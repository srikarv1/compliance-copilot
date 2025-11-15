# Python Version Compatibility

## ⚠️ Important: Python 3.13 Compatibility

Python 3.13 is very new (released October 2024) and some packages may not have full support yet. You're experiencing build issues with:

- `pydantic-core` - needs newer version for Python 3.13
- `tiktoken` - may need Rust compiler or newer version

## Recommended Solutions

### Option 1: Use Python 3.11 or 3.12 (Recommended)

These versions are fully tested and supported by all packages:

```bash
# Install Python 3.11 or 3.12 using pyenv
brew install pyenv
pyenv install 3.11.9
# or
pyenv install 3.12.7

# Create virtual environment with specific version
pyenv local 3.11.9
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Continue with Python 3.13

If you want to use Python 3.13, try these steps:

```bash
# 1. Upgrade pip first
pip install --upgrade pip

# 2. Install Rust (required for tiktoken)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# 3. Try installing with updated requirements
pip install -r requirements.txt

# 4. If pydantic still fails, try installing latest version
pip install "pydantic>=2.9.0" --upgrade
```

### Option 3: Use Docker (Easiest)

Docker uses Python 3.11 by default, avoiding all compatibility issues:

```bash
docker-compose up --build
```

## Quick Fix for Current Error

Try this sequence:

```bash
cd backend
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Rust for tiktoken
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install with updated requirements
pip install -r requirements.txt
```

If issues persist, **strongly recommend using Python 3.11 or 3.12** for best compatibility.

