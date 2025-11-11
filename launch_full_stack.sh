#!/bin/bash
# Launch full EEG burst recording stack
# Opens 2 terminal windows: Realtime Viewer + Burst Recorder

set -e

echo "========================================="
echo "EEG Burst Recording Stack Launcher"
echo "========================================="
echo ""

# Check if Neurable Research Kit is running
echo "⚠️  Before continuing, make sure:"
echo "   1. MW75 Neuro headphones are connected"
echo "   2. Neurable Research Kit app is running"
echo "   3. EEG streaming is started"
echo ""
read -p "Press ENTER when ready..."

echo ""
echo "Starting components..."
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VIEWER_DIR="$HOME/Downloads/eeg-realtime-viewer"

# Check if viewer exists
if [ ! -d "$VIEWER_DIR" ]; then
    echo "❌ Realtime viewer not found at: $VIEWER_DIR"
    echo "   Extracting viewer..."
    cd ~/Downloads
    unzip -q eeg-realtime-viewer.zip
fi

# Launch Realtime Viewer in new terminal
echo "1. Launching Realtime Viewer..."
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$VIEWER_DIR' && source venv/bin/activate 2>/dev/null || (python3 -m venv venv && source venv/bin/activate && pip install -q -r requirements.txt) && python run_viewer.py --source lsl"
end tell
EOF

sleep 2

# Launch Burst Recorder in new terminal
echo "2. Launching Burst Recorder..."
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$SCRIPT_DIR' && source venv/bin/activate 2>/dev/null || (python3 -m venv venv && source venv/bin/activate && pip install -q -r requirements.txt) && python burst_recorder.py --threshold-rms 50 --threshold-p2p 100"
end tell
EOF

echo ""
echo "✓ Both components launched in separate terminal windows"
echo ""
echo "You should see:"
echo "  - Terminal 1: Realtime EEG visualization"
echo "  - Terminal 2: Burst detector monitoring"
echo ""
echo "When bursts are detected:"
echo "  - Vertical markers appear in viewer"
echo "  - Burst files saved to burst_data/"
echo ""
echo "Press Ctrl+C in each terminal to stop"
echo "========================================="
