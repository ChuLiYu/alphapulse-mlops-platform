#!/bin/bash
# Setup automated data collection using launchd (macOS) or cron (Linux)

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "🔧 Setup Automated Data Collection"
echo "============================================================"
echo ""
echo "Project Directory: $PROJECT_DIR"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected: macOS"
    echo ""
    
    # Create launchd plist
    PLIST_NAME="com.alphapulse.datacollection"
    PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
    
    echo "Creating launchd configuration..."
    
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${PROJECT_DIR}/scripts/auto_collect_data.sh</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>2</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>14</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>20</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    
    <key>StandardOutPath</key>
    <string>/tmp/alphapulse_auto_collect.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/alphapulse_auto_collect_error.log</string>
    
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
</dict>
</plist>
EOF
    
    echo -e "${GREEN}✅ Created: $PLIST_PATH${NC}"
    echo ""
    echo "Schedule: Data collection will run at 02:00, 08:00, 14:00, 20:00 daily"
    echo ""
    
    # Load the plist
    echo "Loading launchd job..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Automated collection enabled!${NC}"
        echo ""
        echo "Commands:"
        echo "  • Check status: launchctl list | grep alphapulse"
        echo "  • View logs: tail -f /tmp/alphapulse_auto_collect.log"
        echo "  • Disable: launchctl unload $PLIST_PATH"
        echo "  • Manual run: $PROJECT_DIR/scripts/auto_collect_data.sh"
    else
        echo -e "${YELLOW}⚠️ Failed to load launchd job${NC}"
    fi
    
else
    echo "Detected: Linux/Unix"
    echo ""
    
    # Create cron entry
    CRON_CMD="0 2,8,14,20 * * * cd $PROJECT_DIR && ./scripts/auto_collect_data.sh"
    
    echo "Cron entry to add:"
    echo "  $CRON_CMD"
    echo ""
    
    # Check if entry already exists
    if crontab -l 2>/dev/null | grep -q "auto_collect_data.sh"; then
        echo -e "${YELLOW}⚠️ Cron entry already exists${NC}"
    else
        echo "Adding to crontab..."
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Automated collection enabled!${NC}"
            echo ""
            echo "Commands:"
            echo "  • View crontab: crontab -l"
            echo "  • Edit crontab: crontab -e"
            echo "  • Remove: crontab -e (delete the line)"
            echo "  • Manual run: $PROJECT_DIR/scripts/auto_collect_data.sh"
        else
            echo -e "${YELLOW}⚠️ Failed to add cron entry${NC}"
            echo "Please add manually: crontab -e"
            echo "Add this line: $CRON_CMD"
        fi
    fi
fi

echo ""
echo "============================================================"
echo "✅ Setup Complete"
echo "============================================================"
echo ""
echo "Test the script manually first:"
echo "  cd $PROJECT_DIR"
echo "  ./scripts/auto_collect_data.sh"
