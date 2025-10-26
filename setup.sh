#!/bin/bash

# RFID Music System - Robust Setup Script
# Handles uv installation and PATH issues gracefully (supports fish shell)

echo "🎵 RFID Music System - Setup"
echo "============================"

# Function to check if uv is available
check_uv() {
    if command -v uv &> /dev/null; then
        return 0
    elif [ -f "$HOME/.local/bin/uv" ]; then
        export PATH="$HOME/.local/bin:$PATH"
        return 0
    elif [ -f "$HOME/.cargo/bin/uv" ]; then
        export PATH="$HOME/.cargo/bin:$PATH"
        return 0
    else
        return 1
    fi
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "📦 Install with: sudo apt install python3"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if uv is available
if ! check_uv; then
    echo "📦 Installing uv (fast Python package manager)..."
    
    # Install uv
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        echo "✅ uv downloaded successfully"
        
        # Try to source the environment for different shells
        if [ -f "$HOME/.local/bin/env" ]; then
            source "$HOME/.local/bin/env"
        elif [ -f "$HOME/.local/bin/env.fish" ] && [ "$SHELL" = "/usr/bin/fish" ]; then
            echo "Fish shell detected. Please run:"
            echo "  source \$HOME/.local/bin/env.fish"
            echo "  ./setup.sh"
            exit 2
        fi
        
        # Check again
        if ! check_uv; then
            echo "⚠️  uv installed but not in PATH"
            echo ""
            if [ "$SHELL" = "/usr/bin/fish" ] || [[ "$SHELL" == *"fish"* ]]; then
                echo "For Fish shell, run:"
                echo "  source \$HOME/.local/bin/env.fish"
            else
                echo "For Bash/Zsh, run:"
                echo "  source \$HOME/.local/bin/env"
                echo "  export PATH=\$HOME/.local/bin:\$PATH"
            fi
            echo ""
            echo "Then run this setup script again."
            exit 2
        fi
    else
        echo "❌ Failed to install uv"
        echo "📖 Manual installation: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
fi

echo "✅ uv found: $(uv --version)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
if [ -f "pyproject.toml" ]; then
    echo "   Trying pyproject.toml..."
    if ! uv pip install -e .; then
        echo "   pyproject.toml failed, falling back to requirements.txt..."
        uv pip install -r requirements.txt
    fi
else
    echo "   Using requirements.txt..."
    uv pip install -r requirements.txt
fi

echo "✅ Dependencies installed"

# Create directories
echo "📁 Creating directories..."
mkdir -p logs static/covers
echo "✅ Directories created"

# Set default environment variables
echo ""
echo "🔧 Configuration:"
echo "   Music directory: ${MUSIC_BASE_PATH:-/home/music} (set MUSIC_BASE_PATH to change)"
echo "   macOS host: ${MACOS_HOST:-192.168.1.100} (set MACOS_HOST to change)" 
echo "   macOS port: ${MACOS_PORT:-5001} (set MACOS_PORT to change)"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Configure your music directory and macOS host IP:"
if [ "$SHELL" = "/usr/bin/fish" ] || [[ "$SHELL" == *"fish"* ]]; then
    echo "      set -x MUSIC_BASE_PATH /path/to/your/music"
    echo "      set -x MACOS_HOST your.macos.ip.address"
else
    echo "      export MUSIC_BASE_PATH=/path/to/your/music"
    echo "      export MACOS_HOST=your.macos.ip.address"
fi
echo ""
echo "   2. Start the system:"
echo "      ./start.sh                 # Start both services"
echo "      ./start.sh web            # Web interface only"  
echo "      ./start.sh rfid           # RFID listener only"
echo ""
echo "   3. Open web interface: http://localhost:5000"
echo ""
echo "🎵 Happy music playing!"