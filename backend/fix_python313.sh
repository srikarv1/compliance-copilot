#!/bin/bash
# Quick fix script for Python 3.13 compatibility issues

echo "🔧 Fixing Python 3.13 compatibility issues..."

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Rust (required for tiktoken)
if ! command -v rustc &> /dev/null; then
    echo "🦀 Installing Rust compiler..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "✅ Rust already installed"
fi

# Try installing with updated requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Done! If you still see errors, consider using Python 3.11 or 3.12."
echo "   See backend/PYTHON_VERSION.md for more options."

