#!/bin/bash

# Advanced Content Tracker - Systemd Service Installer
# Installs the tracker as a user systemd service

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       Content Tracker - Service Installer                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get installation directory
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="${INSTALL_DIR}/venv/bin/python"
SERVICE_NAME="content-tracker"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}Error: Virtual environment not found.${NC}"
    echo "Please run ./install.sh first."
    exit 1
fi

# Create systemd user directory
mkdir -p ~/.config/systemd/user

# Create service file
SERVICE_FILE="$HOME/.config/systemd/user/${SERVICE_NAME}.service"

echo -e "${BLUE}Creating systemd service...${NC}"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Advanced Content Tracker
Documentation=https://github.com/your-repo/content-tracker
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=${VENV_PYTHON} ${INSTALL_DIR}/main.py
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority
Environment=XDG_RUNTIME_DIR=/run/user/%U

# Logging
StandardOutput=append:${INSTALL_DIR}/logs/service.log
StandardError=append:${INSTALL_DIR}/logs/service.error.log

# Resource limits
MemoryMax=2G
CPUQuota=50%

[Install]
WantedBy=default.target
EOF

echo -e "${GREEN}Service file created: ${SERVICE_FILE}${NC}"

# Reload systemd
echo -e "${BLUE}Reloading systemd...${NC}"
systemctl --user daemon-reload

# Enable service
echo -e "${BLUE}Enabling service...${NC}"
systemctl --user enable "${SERVICE_NAME}.service"

# Ask to start service
echo ""
read -p "Start the service now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl --user start "${SERVICE_NAME}.service"
    sleep 2
    
    if systemctl --user is-active --quiet "${SERVICE_NAME}.service"; then
        echo -e "${GREEN}Service started successfully!${NC}"
    else
        echo -e "${RED}Service failed to start. Check logs:${NC}"
        echo "  journalctl --user -u ${SERVICE_NAME}.service -f"
    fi
fi

# Print usage
echo -e "\n${GREEN}Service installed!${NC}"
echo ""
echo "Commands:"
echo "  ${BLUE}systemctl --user start ${SERVICE_NAME}${NC}    # Start service"
echo "  ${BLUE}systemctl --user stop ${SERVICE_NAME}${NC}     # Stop service"
echo "  ${BLUE}systemctl --user restart ${SERVICE_NAME}${NC}  # Restart service"
echo "  ${BLUE}systemctl --user status ${SERVICE_NAME}${NC}   # Check status"
echo ""
echo "View logs:"
echo "  ${BLUE}journalctl --user -u ${SERVICE_NAME} -f${NC}"
echo ""
echo "Disable auto-start:"
echo "  ${BLUE}systemctl --user disable ${SERVICE_NAME}${NC}"
echo ""
