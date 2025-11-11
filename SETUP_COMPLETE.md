# 🎯 EEG Burst Recorder - SETUP COMPLETE

**Created:** November 10, 2025

## ✅ What's Been Built

### Core System
- **Event-Triggered Burst Recorder** (`burst_recorder.py`)
  - Auto-detects EEG bursts when thresholds exceeded
  - Saves pre-burst + post-burst windows
  - Sends LSL markers to visualizer
  - NPZ + JSON output format

### Integration Tools
- **Full Stack Launcher** (`launch_full_stack.sh`)
  - One-command launch of entire system
  - Opens 2 terminals: viewer + recorder
  - Auto-configures environments

### Analysis Tools
- **Burst Analyzer** (`analyze_burst.py`)
  - Load and visualize burst data
  - Calculate statistics per channel
  - Generate publication-ready plots

### Documentation
- **README.md** - Complete reference documentation
- **QUICKSTART.md** - 5-minute setup guide
- **requirements.txt** - Python dependencies

## 📦 Your SDK Assets (Already Downloaded)

Located in `~/Downloads/`:

1. **Neurable Research Kit EEG Visualizer**
   - `Neurable Research Kit EEG Visualizer-Installer-MacOS-Silicon-arm64.dmg` ← Install this
   - Full GUI application for EEG streaming

2. **EEG Realtime Viewer** (Extracted)
   - `eeg-realtime-viewer/` - Python LSL viewer
   - Shows live waveforms + burst markers

3. **TypeScript SDK** (Optional)
   - `typescript-sdk-prod-v0.9.2/` - For web integrations

## 🚀 Next Steps

### 1. Install Neurable Research Kit (One-time, ~5 min)

```bash
open ~/Downloads/Neurable\ Research\ Kit\ EEG\ Visualizer-Installer-MacOS-Silicon-arm64.dmg
```

### 2. Setup Python Environments (One-time, ~2 min)

```bash
# Setup burst recorder
cd ~/Downloads/eeg-burst-recorder
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Test the System (First run)

```bash
# Launch everything
cd ~/Downloads/eeg-burst-recorder
./launch_full_stack.sh
```

**Expected flow:**
1. Opens 2 terminal windows
2. Realtime viewer shows live EEG
3. Burst recorder monitors in background
4. When burst detected → marker appears + data saved

## 🎯 System Architecture

```
MW75 Neuro Headphones
         ↓ Bluetooth
         ↓
[Neurable Research Kit App]
         ↓ LSL Stream (type='EEG')
         ↓
    ┌────┴────┐
    ↓         ↓
[Realtime  [Burst
 Viewer]    Recorder] ← You are here
    ↑         ↓
    │    Burst Data
    │    (NPZ + JSON)
    │         ↓
    └─────[analyze_burst.py]
          ↓
      Visualizations
```

## 📊 Example Workflow

### Recording Session

```bash
# Terminal 1: Start everything
./launch_full_stack.sh

# System runs until you press Ctrl+C
# Bursts saved to: burst_data/
```

### Analyze Results

```bash
# View metadata
cat burst_data/burst_*.json

# Analyze specific burst
python analyze_burst.py burst_data/burst_20251110_123456_0001.npz

# Create plot
python analyze_burst.py burst_data/burst_20251110_123456_0001.npz --save my_burst.png
```

## 🔧 Customization Examples

### Adjust Sensitivity

```bash
# More sensitive (catch smaller bursts)
python burst_recorder.py --threshold-rms 30 --threshold-p2p 60

# Less sensitive (only major events)
python burst_recorder.py --threshold-rms 100 --threshold-p2p 200
```

### Change Burst Window

```bash
# Longer context (2s before, 3s after)
python burst_recorder.py --pre-burst 2.0 --post-burst 3.0
```

### Custom Output Location

```bash
python burst_recorder.py --output-dir ~/Documents/my_eeg_study
```

## 📁 Project Structure

```
eeg-burst-recorder/
├── burst_recorder.py          # Main burst detector
├── analyze_burst.py           # Analysis tool
├── launch_full_stack.sh       # Launcher script
├── requirements.txt           # Python deps
├── README.md                  # Full docs
├── QUICKSTART.md             # Quick start
├── SETUP_COMPLETE.md         # This file
└── burst_data/               # Output directory (created on first run)
    ├── burst_*.npz          # EEG data
    └── burst_*_meta.json    # Metadata
```

## 🎓 Learning Resources

### Understanding the Code

1. **burst_recorder.py:88** - LSL stream connection
2. **burst_recorder.py:155** - Burst detection algorithm
3. **burst_recorder.py:195** - Data saving logic
4. **analyze_burst.py:17** - Loading burst files
5. **analyze_burst.py:42** - Visualization code

### Key Concepts

- **RMS (Root Mean Square)**: Overall signal power
- **P2P (Peak-to-Peak)**: Signal amplitude range
- **LSL (Lab Streaming Layer)**: Real-time data protocol
- **NPZ**: Compressed NumPy array format
- **Circular Buffer**: Pre-burst data capture method

## 🐛 Troubleshooting

### "No EEG stream found"
→ Ensure Neurable Research Kit is running and streaming
→ Check MW75 headphones are connected (blue LED)
→ Try restarting the Research Kit app

### Too many false positives
→ Increase thresholds: `--threshold-rms 80 --threshold-p2p 160`
→ Check headphone fit (poor contact = noise)

### Viewer shows no markers
→ Burst recorder running with markers enabled? (default: yes)
→ Both apps connected to same LSL stream? (should auto-connect)

## 🎉 You're Ready!

All components are built and documented. The system is ready to use with your MW75 Neuro headphones.

**To start recording:**
```bash
cd ~/Downloads/eeg-burst-recorder
./launch_full_stack.sh
```

---

**Questions or Issues?**
- Check README.md for detailed documentation
- Review QUICKSTART.md for setup troubleshooting
- Examine example code in analyze_burst.py
