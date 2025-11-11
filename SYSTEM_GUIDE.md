# EEG Burst Recorder - Complete System Guide

## Current Status: NOT RUNNING
The test we just did completed and stopped automatically after 30 seconds.

---

## How the System Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ 1. NEURABLE RESEARCH KIT (Always On When Headphones On) │
│    - Connects to MW75 Neuro via Bluetooth               │
│    - Streams EEG data via LSL continuously               │
│    - This runs independently, always streaming           │
└────────────────┬────────────────────────────────────────┘
                 │ LSL Stream (type='EEG')
                 │ 500 Hz, 14 channels
                 │ ALWAYS AVAILABLE when headphones are on
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. BURST RECORDER (On-Demand, Event-Triggered)          │
│    - Monitors the LSL stream                            │
│    - Only saves data when thresholds exceeded           │
│    - YOU control when this runs                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ├─→ Saves bursts to files (NPZ + JSON)
                 └─→ Sends LSL markers (for viewer)
```

---

## The Three Operating Modes

### Mode 1: STREAMING ONLY (Current State)
**What's happening:**
- Neurable Research Kit is running
- EEG data flows via LSL
- **NOTHING is being saved** (no recorder running)
- Data disappears unless something is listening

**How to check:**
```bash
# Your headphones are streaming if you see this:
ps aux | grep -i neurable
```

**When to use:**
- When you just want to wear headphones
- When using only the realtime viewer
- When you don't need to save any data

---

### Mode 2: BURST DETECTION (What We Just Tested)
**What's happening:**
- Recorder monitors LSL stream in real-time
- Processes EVERY sample (500 per second × 14 channels = 7,000 data points/sec)
- **Only saves when burst detected** (thresholds exceeded)
- All other data is discarded

**How it works:**
```
Every sample processed:
├─ Check RMS and P2P values
├─ If ANY channel exceeds threshold:
│  ├─ 🔥 BURST DETECTED!
│  ├─ Save 1s pre-burst (from circular buffer)
│  ├─ Capture 2s post-burst
│  ├─ Save to files (NPZ + JSON)
│  └─ Send LSL marker
└─ Otherwise: Discard and move to next sample
```

**Memory usage:**
- Circular buffer: ~2000 samples (~56 KB RAM)
- Most data never touches disk
- Only bursts are saved

**How to run:**
```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate

# Run until you press Ctrl+C
python burst_recorder.py

# Or with time limit
python burst_recorder.py --duration 60  # 60 seconds
```

**How to STOP:**
- Press `Ctrl+C` (keyboard interrupt)
- Or wait for `--duration` to expire
- Or close the terminal window

---

### Mode 3: FULL STACK (Viewer + Recorder)
**What's happening:**
- Terminal 1: Realtime viewer shows live EEG
- Terminal 2: Burst recorder monitors and saves
- When burst detected → vertical marker appears in viewer
- Visual feedback of what's being saved

**How to run:**
```bash
cd ~/Downloads/eeg-burst-recorder
./launch_full_stack.sh
```

**How to STOP:**
- Press `Ctrl+C` in BOTH terminal windows
- Or close both terminal windows

---

## When Data Gets Saved

### ❌ Data NOT Saved:
- When only Neurable Research Kit is running
- When only realtime viewer is running
- Normal EEG activity below thresholds
- When recorder is stopped

### ✅ Data IS Saved:
- Only when burst recorder is running
- Only when thresholds are exceeded
- Each burst creates 2 files:
  - `burst_YYYYMMDD_HHMMSS_NNNN.npz` (EEG data)
  - `burst_YYYYMMDD_HHMMSS_NNNN_meta.json` (metadata)

### Example Timeline:
```
00:00 - Neurable streaming, recorder OFF → Nothing saved
00:10 - Start burst recorder → Monitoring begins
00:15 - Normal EEG activity (below threshold) → Nothing saved
00:20 - Eye blink (high amplitude) → BURST SAVED!
00:25 - Normal activity → Nothing saved
00:30 - Jaw clench (high amplitude) → BURST SAVED!
00:35 - Stop burst recorder (Ctrl+C) → Monitoring stops
00:40 - Neurable still streaming → Nothing saved
```

---

## Threshold Configuration

### Current Defaults:
```bash
--threshold-rms 50.0   # Root Mean Square (µV)
--threshold-p2p 100.0  # Peak-to-Peak amplitude (µV)
```

### What These Mean:

**RMS (Root Mean Square):**
- Overall signal power
- 50 µV = moderate sensitivity
- Lower = more sensitive (more bursts)
- Higher = less sensitive (fewer bursts)

**P2P (Peak-to-Peak):**
- Maximum swing of signal
- 100 µV = moderate sensitivity
- Measures largest deflections

**A burst is triggered when EITHER threshold is exceeded on ANY channel**

### Adjusting Sensitivity:

**More sensitive (catch small events):**
```bash
python burst_recorder.py --threshold-rms 30 --threshold-p2p 60
```

**Less sensitive (only big events):**
```bash
python burst_recorder.py --threshold-rms 100 --threshold-p2p 200
```

**Extreme sensitivity (every artifact):**
```bash
python burst_recorder.py --threshold-rms 10 --threshold-p2p 20
```

**Very conservative (only major activity):**
```bash
python burst_recorder.py --threshold-rms 200 --threshold-p2p 500
```

---

## Burst Window Configuration

### What Gets Saved Per Burst:

```
Time:  [-1.0s] ───────► [0.0s] ─────────────► [+2.0s]
        Pre-burst      Trigger      Post-burst
         500 samples   point        1000 samples
       ◄─────────────────────────────────────►
              Total: 3.0 seconds saved
                   (1500 samples)
```

### Adjusting Windows:

**Longer pre-burst context:**
```bash
python burst_recorder.py --pre-burst 2.0  # 2 seconds before
```

**Longer post-burst capture:**
```bash
python burst_recorder.py --post-burst 5.0  # 5 seconds after
```

**Minimal window (fast):**
```bash
python burst_recorder.py --pre-burst 0.5 --post-burst 1.0
```

**Extended window (comprehensive):**
```bash
python burst_recorder.py --pre-burst 3.0 --post-burst 5.0
```

---

## Control Commands

### Starting the Recorder

**Basic start (infinite):**
```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate
python burst_recorder.py
```

**Timed session:**
```bash
python burst_recorder.py --duration 300  # 5 minutes
```

**Custom output location:**
```bash
python burst_recorder.py --output-dir ~/Documents/my_eeg_study
```

**Silent mode (no LSL markers):**
```bash
python burst_recorder.py --no-markers
```

### Stopping the Recorder

**Method 1: Keyboard (recommended)**
```
Press: Ctrl+C
Result: Clean shutdown, shows summary
```

**Method 2: Terminal close**
```
Close the terminal window
Result: Process killed immediately
```

**Method 3: Kill process**
```bash
# Find process ID
ps aux | grep burst_recorder

# Kill it
kill <PID>
```

### Checking Status

**Is recorder running?**
```bash
ps aux | grep burst_recorder
```

**Is Neurable streaming?**
```bash
ps aux | grep -i neurable
```

**How much data collected?**
```bash
ls -lh ~/Downloads/eeg-burst-recorder/burst_data/
```

**Count bursts:**
```bash
ls ~/Downloads/eeg-burst-recorder/burst_data/*.npz | wc -l
```

---

## Practical Usage Scenarios

### Scenario 1: Quick Test (What We Just Did)
```bash
# 30-second test recording
python burst_recorder.py --duration 30
```
**Result:** 6 bursts captured

### Scenario 2: Meditation Session
```bash
# 20-minute session, sensitive thresholds
python burst_recorder.py --duration 1200 --threshold-rms 30 --threshold-p2p 60
```

### Scenario 3: Focus Work
```bash
# 1-hour session, moderate sensitivity
python burst_recorder.py --duration 3600 --threshold-rms 50 --threshold-p2p 100
```

### Scenario 4: All-Day Monitoring
```bash
# Infinite recording, save to dated folder
mkdir -p ~/eeg_data/$(date +%Y%m%d)
python burst_recorder.py --output-dir ~/eeg_data/$(date +%Y%m%d)
```

### Scenario 5: Research Study
```bash
# Very conservative, only major events
python burst_recorder.py \
  --threshold-rms 150 \
  --threshold-p2p 300 \
  --pre-burst 2.0 \
  --post-burst 5.0 \
  --output-dir ~/research/participant_01
```

---

## Data Management

### Where Files Go
```
~/Downloads/eeg-burst-recorder/
└── burst_data/                          # Default location
    ├── burst_20251110_224830_0001.npz   # EEG data (66 KB)
    ├── burst_20251110_224830_0001_meta.json  # Metadata (2 KB)
    ├── burst_20251110_224835_0002.npz
    ├── burst_20251110_224835_0002_meta.json
    └── ...
```

### Storage Usage

**Per burst:**
- NPZ file: ~60-70 KB
- JSON file: ~2 KB
- Total: ~65-72 KB per burst

**Hourly estimates:**
- Low activity (5 bursts/hour): ~350 KB
- Moderate (20 bursts/hour): ~1.4 MB
- High activity (60 bursts/hour): ~4.3 MB

**Daily estimates (8 hours):**
- Low: ~2.7 MB
- Moderate: ~11 MB
- High: ~35 MB

### Cleaning Up

**Delete all bursts:**
```bash
rm ~/Downloads/eeg-burst-recorder/burst_data/*
```

**Archive old bursts:**
```bash
mkdir -p ~/eeg_archive/$(date +%Y%m%d)
mv ~/Downloads/eeg-burst-recorder/burst_data/* ~/eeg_archive/$(date +%Y%m%d)/
```

**Delete bursts older than 7 days:**
```bash
find ~/Downloads/eeg-burst-recorder/burst_data/ -mtime +7 -delete
```

---

## Advanced Features

### Burst Cooldown
**Built-in anti-spam:** Minimum 3 seconds between bursts
- Prevents saving the same event multiple times
- Can't trigger more than 20 bursts/minute

### Circular Buffer
**Pre-burst capture magic:**
- Always maintains last ~4 seconds of data in RAM
- When burst detected, saves the 1s before threshold crossing
- No data loss at burst onset

### LSL Markers
**Event synchronization:**
- Each burst sends `BURST_<burst_id>` marker
- Realtime viewer displays as vertical line
- Other LSL tools can receive these events
- Can be disabled with `--no-markers`

### Multi-Channel Detection
**Any channel can trigger:**
- Monitors all 14 channels simultaneously
- Burst detected if ANY channel exceeds threshold
- Saves which channels triggered in metadata
- Non-triggering channels still saved for context

---

## Troubleshooting

### "No EEG stream found"
**Cause:** Neurable Research Kit not running or not streaming
**Fix:**
1. Open Neurable Research Kit app
2. Put on MW75 headphones
3. Click "Start Streaming"
4. Wait 5 seconds, try again

### Too Many Bursts
**Cause:** Thresholds too low or lots of artifacts
**Fix:**
```bash
# Increase thresholds
python burst_recorder.py --threshold-rms 100 --threshold-p2p 200

# Or check headphone fit (poor contact = noise)
```

### No Bursts Detected
**Cause:** Thresholds too high or very quiet EEG
**Fix:**
```bash
# Lower thresholds
python burst_recorder.py --threshold-rms 20 --threshold-p2p 40

# Or generate some activity (blink, move jaw)
```

### Disk Full
**Cause:** Too many bursts saved
**Fix:**
```bash
# Check disk space
df -h ~

# Delete old bursts
rm ~/Downloads/eeg-burst-recorder/burst_data/*.npz
rm ~/Downloads/eeg-burst-recorder/burst_data/*.json
```

### Recorder Won't Stop
**Cause:** Process hung
**Fix:**
```bash
# Force kill
pkill -9 -f burst_recorder
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│              EEG BURST RECORDER                     │
├─────────────────────────────────────────────────────┤
│ START:    python burst_recorder.py                  │
│ STOP:     Ctrl+C                                    │
│ STATUS:   ps aux | grep burst_recorder              │
│ COUNT:    ls burst_data/*.npz | wc -l               │
├─────────────────────────────────────────────────────┤
│ More sensitive:   --threshold-rms 30                │
│ Less sensitive:   --threshold-rms 100               │
│ Time limit:       --duration 300                    │
│ Custom location:  --output-dir ~/my_data            │
├─────────────────────────────────────────────────────┤
│ Analyze burst:                                      │
│   python analyze_burst.py burst_data/burst_*.npz    │
│                                                     │
│ Full stack:                                         │
│   ./launch_full_stack.sh                           │
└─────────────────────────────────────────────────────┘
```

---

## Key Concepts Summary

1. **Neurable streams continuously** - Your headphones + Research Kit always send data
2. **Recorder monitors on-demand** - You control when to watch for bursts
3. **Event-triggered saving** - Only interesting moments get saved to disk
4. **Threshold-based detection** - You define what "interesting" means
5. **Circular buffer** - Pre-burst data captured automatically
6. **Simple start/stop** - One command to start, Ctrl+C to stop

---

**Current State:** NOT RUNNING
**To start monitoring:** `cd ~/Downloads/eeg-burst-recorder && source venv/bin/activate && python burst_recorder.py`
