#!/bin/bash

# Custom ChatGPT API Installation Script for Raspberry Pi
# Run with: bash install.sh

set -e

echo "🚀 Installing Custom ChatGPT API on Raspberry Pi..."
echo "=================================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This script is optimized for Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo "🐍 Installing Python and pip..."
sudo apt install python3 python3-pip python3-venv python3-full -y

# Install system dependencies for Playwright
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libx11-xcb1 \
    libxcb-dri3-0

# Create project directory
PROJECT_DIR="/home/pi/ChatAPI"
echo "📁 Creating project directory: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Copy project files (assuming they're in current directory)
echo "📋 Copying project files..."
cp -r . "$PROJECT_DIR/" 2>/dev/null || echo "Files already in place"

# Create virtual environment
echo "🔒 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
./venv/bin/playwright install chromium

# Make scripts executable
chmod +x start_server.py
chmod +x test_api.py

# Create log directory
mkdir -p logs

echo ""
echo "✅ Installation completed!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start the server: python3 start_server.py"
echo "3. Test the API: python3 test_api.py"
echo "4. Configure port forwarding on your router"
echo "5. Access from internet: http://YOUR_PUBLIC_IP:8000"
echo ""
echo "📖 See README.md for detailed instructions"
echo ""
echo "🔧 To run as a service:"
echo "   sudo cp chatgpt-api.service /etc/systemd/system/"
echo "   sudo systemctl enable chatgpt-api.service"
echo "   sudo systemctl start chatgpt-api.service"
