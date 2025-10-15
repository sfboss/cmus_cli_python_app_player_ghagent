#!/bin/bash
# Installation script for CMUS Rich

set -e

echo "========================================="
echo "CMUS Rich Installation Script"
echo "========================================="
echo

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.10"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "Error: Python 3.10+ is required (found Python $python_version)"
    exit 1
fi
echo "✓ Python $python_version found"

# Check for CMUS
echo
echo "Checking for CMUS..."
if ! command -v cmus &> /dev/null; then
    echo "Warning: CMUS not found. Please install CMUS first:"
    echo "  Ubuntu/Debian: sudo apt-get install cmus"
    echo "  Fedora: sudo dnf install cmus"
    echo "  macOS: brew install cmus"
    echo "  Arch: sudo pacman -S cmus"
    echo
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ CMUS found"
fi

# Create virtual environment (optional)
echo
read -p "Create virtual environment? (recommended) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Virtual environment created and activated"
fi

# Install dependencies
echo
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Install the package
echo
echo "Installing CMUS Rich..."
pip install -e .
echo "✓ CMUS Rich installed"

# Create directories
echo
echo "Creating configuration directories..."
mkdir -p ~/.config/cmus-rich
mkdir -p ~/.cache/cmus-rich
mkdir -p ~/.local/share/cmus-rich
echo "✓ Directories created"

# Create default configuration
echo
echo "Creating default configuration..."
python3 -c "from cmus_rich.core.config import ConfigManager; ConfigManager()"
echo "✓ Default configuration created at ~/.config/cmus-rich/config.toml"

echo
echo "========================================="
echo "Installation complete!"
echo "========================================="
echo
echo "To get started:"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  1. Activate the virtual environment: source venv/bin/activate"
fi
echo "  2. Start CMUS Rich: cmus-rich"
echo "  3. Configure: edit ~/.config/cmus-rich/config.toml"
echo
echo "For more information, see the README.md file"
echo
