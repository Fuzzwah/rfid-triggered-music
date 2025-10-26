#!/bin/bash

# RFID Music System - Linux Host Setup Script
# This script sets up the Linux RFID + Web Host environment using uv

echo "Setting up RFID Music System - Linux Host"
echo "=========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Install with: sudo apt install python3"
    exit 1
fi

# Check if uv is installed, if not, install it
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv (fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Check if installation succeeded
    if ! command -v uv &> /dev/null; then
        echo "Error: Failed to install uv"
        echo "Please install uv manually: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    
    echo "✓ uv installed successfully"
else
    echo "✓ uv is already installed"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv
else
    echo "✓ Virtual environment already exists"
fi

# Install dependencies using uv
echo "Installing Python packages with uv..."
if [ -f "pyproject.toml" ]; then
    echo "Using pyproject.toml for dependency management..."
    uv pip install -e .
else
    echo "Falling back to requirements.txt..."
    uv pip install -r requirements.txt
fi

# Create directories
echo "Creating directories..."
mkdir -p logs
mkdir -p static/covers

# Set environment variables (you may want to customize these)
export SECRET_KEY="your-secret-key-change-in-production"
export MUSIC_BASE_PATH="/home/music"  # Change to your music directory
export MACOS_HOST="192.168.1.100"    # Change to your macOS host IP
export MACOS_PORT="5001"

echo ""
echo "Setup complete!"
echo ""
echo "Configuration:"
echo "  Music directory: $MUSIC_BASE_PATH"
echo "  macOS host: $MACOS_HOST:$MACOS_PORT"
echo ""
echo "To start the system:"
echo "  1. Start the Flask app: ./start_webapp.sh"
echo "  2. Start the RFID listener: ./start_rfid_listener.sh"
echo ""
echo "Make sure to:"
echo "  1. Update environment variables in the scripts as needed"
echo "  2. Ensure your music directory exists and contains subdirectories with MP3 files"
echo "  3. Configure your RFID reader to act as a keyboard input device"
echo "  4. Set up the macOS playback host"