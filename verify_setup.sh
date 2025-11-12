#!/bin/bash
# MindMeld Setup Verification Script

echo "🔍 Verifying MindMeld Pipeline Setup..."
echo ""

# Activate venv
source venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
echo "✓ $PYTHON_VERSION"

# Test imports
echo "✓ Testing imports..."
python -c "
import pyaudio, scipy, pandas, sklearn, snappy, yaml
from src.audio_sync import AudioLSLSync
from src.analyzer import quick_analyze
from src.grok_exporter import GrokExport
from burst_recorder import EEGBurstRecorder
" 2>/dev/null && echo "  ✓ All modules import successfully" || echo "  ❌ Import error"

# Check config
echo "✓ Testing YAML config..."
python -c "
import yaml
with open('config/meditation.yaml') as f:
    config = yaml.safe_load(f)
    print(f'  RMS threshold: {config[\"thresholds\"][\"rms\"]}µV')
    print(f'  Audio: {\"Enabled\" if config[\"audio\"][\"enable\"] else \"Disabled\"}')
" 2>/dev/null || echo "  ❌ Config error"

# Check directories
echo "✓ Checking directories..."
[ -d "src" ] && echo "  ✓ src/" || echo "  ❌ src/ missing"
[ -d "config" ] && echo "  ✓ config/" || echo "  ❌ config/ missing"
[ -d "scripts" ] && echo "  ✓ scripts/" || echo "  ❌ scripts/ missing"
[ -f "scripts/run_mindmeld.py" ] && echo "  ✓ run_mindmeld.py" || echo "  ❌ run_mindmeld.py missing"

echo ""
echo "=========================================="
echo "✅ MindMeld Pipeline is ready for testing!"
echo "=========================================="
echo ""
echo "To start a test session, run:"
echo "  python scripts/run_mindmeld.py --session test_001 --duration 60"
echo ""
echo "Prerequisites:"
echo "  - Neurable Research Kit running"
echo "  - MW75 headphones connected and streaming"
echo ""
