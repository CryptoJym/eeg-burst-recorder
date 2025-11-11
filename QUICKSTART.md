# 5-Minute Quick Start

## Prerequisites Installed ✓

You already have:
- ✓ Neurable MW75 Neuro headphones
- ✓ Neurable Research Kit installer (Downloads folder)
- ✓ EEG Realtime Viewer (Downloads folder)
- ✓ Burst Recorder (this directory)

## Step 1: Install Neurable Research Kit (One-time)

```bash
open ~/Downloads/Neurable\ Research\ Kit\ EEG\ Visualizer-Installer-MacOS-Silicon-arm64.dmg
```

Follow the installer, then:
1. Open Neurable Research Kit from Applications
2. Put on MW75 Neuro headphones
3. Click "Start Streaming"

## Step 2: Setup Python Environments (One-time)

```bash
# Setup burst recorder
cd ~/Downloads/eeg-burst-recorder
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Setup realtime viewer
cd ~/Downloads/eeg-realtime-viewer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

## Step 3: Launch Everything (Every Session)

**Option A: Automatic (Easiest)**
```bash
cd ~/Downloads/eeg-burst-recorder
./launch_full_stack.sh
```

**Option B: Manual Control**

Terminal 1 - Realtime Viewer:
```bash
cd ~/Downloads/eeg-realtime-viewer
source venv/bin/activate
python run_viewer.py --source lsl
```

Terminal 2 - Burst Recorder:
```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate
python burst_recorder.py
```

## What You'll See

1. **Realtime Viewer** - Live EEG waveforms from all channels
2. **Burst Recorder** - Console showing monitoring status
3. **When burst detected**:
   - Console: "🔥 BURST DETECTED!"
   - Viewer: Red vertical line appears
   - Files saved to `burst_data/`

## Customize Thresholds

Default thresholds might be too sensitive/insensitive. Adjust:

```bash
# More sensitive (catch smaller bursts)
python burst_recorder.py --threshold-rms 30 --threshold-p2p 60

# Less sensitive (only big bursts)
python burst_recorder.py --threshold-rms 80 --threshold-p2p 160

# Balanced (default)
python burst_recorder.py --threshold-rms 50 --threshold-p2p 100
```

## View Your Data

```bash
# List burst files
ls -lh burst_data/

# View metadata
cat burst_data/burst_*.json | head -50

# Analyze in Python
python3
>>> import numpy as np
>>> burst = np.load('burst_data/burst_20251110_123456_0001.npz')
>>> data = burst['data']
>>> print(f"Shape: {data.shape}")  # (samples, channels)
```

## Troubleshooting

**"No EEG stream found"**
- Check Neurable Research Kit is open and streaming
- Verify headphones connected (blue LED)
- Try unplugging/replugging USB dongle

**Too many bursts**
- Increase thresholds: `--threshold-rms 80 --threshold-p2p 160`
- Check electrode contact (adjust headphones)

**No bursts detected**
- Lower thresholds: `--threshold-rms 30 --threshold-p2p 60`
- Blink eyes rapidly (should trigger frontal channels)
- Clench jaw (should trigger central channels)

## Next Steps

- See `README.md` for full documentation
- Check `burst_data/` for your recordings
- Integrate with your analysis pipeline
- Customize detection algorithm in `burst_recorder.py`

---

**Ready to record!** 🎯
