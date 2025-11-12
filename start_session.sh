#!/bin/bash
# Interactive MindMeld Session Starter

echo "============================================================"
echo "🧠 MindMeld Pipeline - Guided Session Starter"
echo "============================================================"
echo ""

# Activate venv
source venv/bin/activate

# Prerequisites checklist
echo "📋 Pre-flight Checklist:"
echo ""
echo "Before we start, make sure:"
echo "  1. Neurable Research Kit app is OPEN"
echo "  2. MW75 headphones are ON and PAIRED"
echo "  3. You see EEG data STREAMING in the Neurable app"
echo "  4. Headphones are on your head (or nearby for testing)"
echo ""
read -p "✓ All set? Press ENTER to continue (or Ctrl+C to exit)..."

echo ""
echo "============================================================"
echo "🎯 Choose Your Session Type:"
echo "============================================================"
echo ""
echo "  1) Quick Test (30 seconds) - RECOMMENDED FOR FIRST TIME"
echo "  2) Meditation Mode (5 minutes) - Calm, eyes-closed recording"
echo "  3) Conversation Mode (3 minutes) - Continuous chunks while talking"
echo "  4) Custom - I'll specify my own parameters"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
  1)
    SESSION_NAME="quick_test_$(date +%Y%m%d_%H%M%S)"
    echo ""
    echo "✓ Starting 30-second quick test"
    echo "✓ Session: $SESSION_NAME"
    echo ""
    echo "What you'll see:"
    echo "  - Connection to EEG stream (2-5 seconds)"
    echo "  - Monitoring for bursts (25 seconds)"
    echo "  - Session summary with file locations"
    echo ""
    echo "What to do:"
    echo "  - Just sit there, you can blink, think, or relax"
    echo "  - Any brain activity might trigger a burst"
    echo "  - Press Ctrl+C to stop early"
    echo ""
    read -p "Press ENTER to start..."
    python scripts/run_mindmeld.py --session "$SESSION_NAME" --mode burst --duration 30
    ;;

  2)
    SESSION_NAME="meditation_$(date +%Y%m%d_%H%M%S)"
    echo ""
    echo "✓ Starting 5-minute meditation session"
    echo "✓ Session: $SESSION_NAME"
    echo ""
    echo "What to do:"
    echo "  - Sit comfortably"
    echo "  - Close your eyes or meditate"
    echo "  - Breathe naturally"
    echo "  - System will auto-detect theta/alpha waves"
    echo ""
    echo "Expected bursts: 5-20 during the session"
    echo ""
    read -p "Press ENTER to start..."
    python scripts/run_mindmeld.py --session "$SESSION_NAME" --mode burst --duration 300
    ;;

  3)
    SESSION_NAME="conversation_$(date +%Y%m%d_%H%M%S)"
    echo ""
    echo "✓ Starting 3-minute conversation mode"
    echo "✓ Session: $SESSION_NAME"
    echo ""
    echo "What to do:"
    echo "  - Talk out loud (or have a conversation)"
    echo "  - System records 30-second chunks automatically"
    echo "  - Good for podcasts, talks, voice analysis"
    echo ""
    echo "Expected chunks: 6 (one every 30 seconds)"
    echo ""
    read -p "Press ENTER to start..."
    python scripts/run_mindmeld.py --session "$SESSION_NAME" --mode continuous --duration 180
    ;;

  4)
    echo ""
    echo "Custom session parameters:"
    read -p "Session name (e.g., my_session): " SESSION_NAME
    echo ""
    echo "Mode:"
    echo "  burst      - Detects and saves when threshold exceeded"
    echo "  continuous - Saves fixed chunks every 30 seconds"
    read -p "Mode (burst/continuous): " MODE
    read -p "Duration in seconds (e.g., 60): " DURATION
    read -p "Disable audio? (yes/no): " DISABLE_AUDIO

    CMD="python scripts/run_mindmeld.py --session $SESSION_NAME --mode $MODE --duration $DURATION"
    if [ "$DISABLE_AUDIO" = "yes" ]; then
      CMD="$CMD --no-audio"
    fi

    echo ""
    echo "✓ Running: $CMD"
    echo ""
    read -p "Press ENTER to start..."
    eval $CMD
    ;;

  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

# Post-session summary
echo ""
echo "============================================================"
echo "✅ Session Complete!"
echo "============================================================"
echo ""
echo "📁 Your data is in: burst_data/$SESSION_NAME/"
echo ""
echo "🔍 Quick checks:"
echo ""
echo "View files:"
echo "  ls -lh burst_data/$SESSION_NAME/"
echo ""
echo "Read metadata (human-readable):"
echo "  cat burst_data/$SESSION_NAME/*_meta.json | head -30"
echo ""
echo "See ML insights (decompress Grok export):"
echo "  cd burst_data/$SESSION_NAME"
echo "  python -c \"import snappy; print(snappy.uncompress(open('\$(ls burst_*.json.snappy | head -1)','rb').read()).decode())\" | head -50"
echo ""
echo "============================================================"
echo ""
echo "📖 For detailed guide, see: QUICK_START_GUIDE.md"
echo ""
