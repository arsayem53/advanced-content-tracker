#!/bin/bash

# Advanced Content Tracker - Installation Script
# This script installs all dependencies and sets up the environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║          Advanced Content Tracker - Installer             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root. Consider running as normal user.${NC}"
fi

# Detect package manager
detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt"
        INSTALL_CMD="sudo apt-get install -y"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        INSTALL_CMD="sudo dnf install -y"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        INSTALL_CMD="sudo pacman -S --noconfirm"
    elif command -v zypper &> /dev/null; then
        PKG_MANAGER="zypper"
        INSTALL_CMD="sudo zypper install -y"
    else
        echo -e "${RED}Error: No supported package manager found.${NC}"
        echo "Supported: apt, dnf, pacman, zypper"
        exit 1
    fi
    echo -e "${GREEN}Detected package manager: ${PKG_MANAGER}${NC}"
}

# Install system dependencies
install_system_deps() {
    echo -e "\n${BLUE}Installing system dependencies...${NC}"
    
    case $PKG_MANAGER in
        apt)
            sudo apt-get update
            $INSTALL_CMD \
                python3 \
                python3-pip \
                python3-venv \
                tesseract-ocr \
                tesseract-ocr-eng \
                libx11-dev \
                libxext-dev \
                libxss-dev \
                xdotool \
                xprintidle \
                scrot \
                libnotify-bin \
                python3-dbus \
                libgirepository1.0-dev \
                gir1.2-notify-0.7
            ;;
        dnf)
            $INSTALL_CMD \
                python3 \
                python3-pip \
                python3-virtualenv \
                tesseract \
                tesseract-langpack-eng \
                libX11-devel \
                libXext-devel \
                libXScrnSaver-devel \
                xdotool \
                xprintidle \
                scrot \
                libnotify \
                python3-dbus \
                gobject-introspection-devel
            ;;
        pacman)
            $INSTALL_CMD \
                python \
                python-pip \
                python-virtualenv \
                tesseract \
                tesseract-data-eng \
                libx11 \
                libxext \
                libxss \
                xdotool \
                xprintidle \
                scrot \
                libnotify \
                python-dbus \
                gobject-introspection
            ;;
        zypper)
            $INSTALL_CMD \
                python3 \
                python3-pip \
                python3-virtualenv \
                tesseract-ocr \
                tesseract-ocr-traineddata-english \
                libX11-devel \
                libXext-devel \
                libXScrnSaver-devel \
                xdotool \
                scrot \
                libnotify \
                python3-dbus-python \
                gobject-introspection-devel
            ;;
    esac
    
    echo -e "${GREEN}System dependencies installed.${NC}"
}

# Install Wayland dependencies (optional)
install_wayland_deps() {
    echo -e "\n${BLUE}Installing Wayland support (optional)...${NC}"
    
    case $PKG_MANAGER in
        apt)
            $INSTALL_CMD grim slurp wl-clipboard || true
            ;;
        dnf)
            $INSTALL_CMD grim slurp wl-clipboard || true
            ;;
        pacman)
            $INSTALL_CMD grim slurp wl-clipboard || true
            ;;
        zypper)
            $INSTALL_CMD grim slurp wl-clipboard || true
            ;;
    esac
    
    echo -e "${GREEN}Wayland support installed (if available).${NC}"
}

# Create virtual environment
setup_venv() {
    echo -e "\n${BLUE}Setting up Python virtual environment...${NC}"
    
    if [ -d "venv" ]; then
        echo "Virtual environment already exists."
    else
        python3 -m venv venv
        echo "Virtual environment created."
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip wheel setuptools
    
    echo -e "${GREEN}Virtual environment ready.${NC}"
}

# Install Python dependencies
install_python_deps() {
    echo -e "\n${BLUE}Installing Python dependencies...${NC}"
    
    source venv/bin/activate
    
    # Install base requirements
    pip install -r requirements.txt
    
    echo -e "${GREEN}Python dependencies installed.${NC}"
}

# Install ML models (optional, large download)
install_ml_models() {
    echo -e "\n${YELLOW}ML models installation (optional)${NC}"
    echo "This will download large model files (~500MB - 2GB)."
    read -p "Install ML models for better accuracy? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Downloading ML models...${NC}"
        source venv/bin/activate
        
        # Download CLIP model (will be cached by transformers)
        python3 -c "
from transformers import CLIPProcessor, CLIPModel
print('Downloading CLIP model...')
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
print('CLIP model downloaded.')
" || echo "CLIP download skipped (optional)"
        
        # NudeNet will download on first use
        echo -e "${GREEN}ML models installed.${NC}"
    else
        echo "Skipping ML models. Detection will use rule-based methods."
    fi
}

# Create necessary directories
create_directories() {
    echo -e "\n${BLUE}Creating directories...${NC}"
    
    mkdir -p data/screenshots
    mkdir -p data/reports
    mkdir -p logs
    mkdir -p models/clip
    mkdir -p models/nudenet
    
    echo -e "${GREEN}Directories created.${NC}"
}

# Set up configuration
setup_config() {
    echo -e "\n${BLUE}Setting up configuration...${NC}"
    
    if [ ! -f "config.yaml" ]; then
        echo "Configuration file already exists."
    else
        echo "Using default configuration."
    fi
    
    # Create user config directory
    mkdir -p ~/.config/content-tracker
    
    echo -e "${GREEN}Configuration ready.${NC}"
}

# Create desktop entry
create_desktop_entry() {
    echo -e "\n${BLUE}Creating desktop entry...${NC}"
    
    DESKTOP_FILE="$HOME/.local/share/applications/content-tracker.desktop"
    ICON_PATH="$(pwd)/assets/icon.png"
    
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Content Tracker
Comment=Track and analyze your digital activities
Exec=$(pwd)/venv/bin/python $(pwd)/main.py
Icon=${ICON_PATH}
Terminal=false
Type=Application
Categories=Utility;Monitor;
StartupNotify=true
EOF
    
    chmod +x "$DESKTOP_FILE"
    
    echo -e "${GREEN}Desktop entry created.${NC}"
}

# Run tests
run_tests() {
    echo -e "\n${BLUE}Running quick tests...${NC}"
    
    source venv/bin/activate
    
    # Test imports
    python3 -c "
import sys
sys.path.insert(0, '.')

print('Testing imports...')
from src.utils.config import get_config
from src.storage.database import get_database
from src.core.screenshot import ScreenshotCapture
print('✓ All imports successful')
" || {
        echo -e "${RED}Import test failed!${NC}"
        exit 1
    }
    
    echo -e "${GREEN}All tests passed.${NC}"
}

# Print completion message
print_completion() {
    echo -e "\n${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║          Installation Complete!                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo "To start the tracker:"
    echo "  1. Activate virtual environment:"
    echo "     ${BLUE}source venv/bin/activate${NC}"
    echo ""
    echo "  2. Run the tracker:"
    echo "     ${BLUE}python main.py${NC}              # Foreground mode"
    echo "     ${BLUE}python main.py --daemon${NC}     # Background mode"
    echo "     ${BLUE}python main.py --test${NC}       # Run detection test"
    echo ""
    echo "  3. Check status:"
    echo "     ${BLUE}python main.py --status${NC}"
    echo ""
    echo "  4. Generate report:"
    echo "     ${BLUE}python main.py --report${NC}"
    echo ""
    echo "For systemd service installation:"
    echo "     ${BLUE}./install_service.sh${NC}"
    echo ""
}

# Main installation flow
main() {
    echo "Starting installation..."
    
    detect_package_manager
    install_system_deps
    install_wayland_deps
    create_directories
    setup_venv
    install_python_deps
    setup_config
    install_ml_models
    create_desktop_entry
    run_tests
    print_completion
}

# Run main
main "$@"
