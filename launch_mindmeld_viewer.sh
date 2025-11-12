#!/bin/bash
# Launch MindMeld Session Viewer

cd "$(dirname "$0")"

echo "============================================================"
echo "🧠 MindMeld Session Viewer"
echo "============================================================"
echo ""
echo "Starting web server..."
echo ""

# Activate venv
source venv/bin/activate

# Check if Flask is installed
python -c "import flask" 2>/dev/null || {
    echo "Installing Flask..."
    pip install flask -q
}

# Launch viewer
python server/mindmeld_viewer.py
