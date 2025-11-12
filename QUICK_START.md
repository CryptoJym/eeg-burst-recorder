# MindMeld Quick Start - Audio Panel & Grok Integration

**Updated**: January 11, 2025

---

## ⚠️ Issue #1: Audio Panel Not Visible

### Problem
You're not seeing the **"🎤 Audio Sync (LSL Stream)"** panel at the bottom of the UI.

### Solution: Hard Refresh Your Browser

**Mac/Linux**: Press `Cmd + Shift + R`
**Windows**: Press `Ctrl + Shift + R`

Or manually clear cache:
1. Open browser DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### What You Should See After Refresh

The UI has **4 main panels** (scroll down to see all):

```
┌─────────────────────────────────────────────┐
│ 1. CONNECTION STATUS (Top)                  │
│    🟢 Connected to Server                   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 2. SESSION CONTROLS                          │
│    [Session Name] [Thresholds]              │
│    [Start Recording] [Stop Recording]       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 3. SPECTRAL ANALYSIS (Brain Bands)          │
│    Delta   [████████████░░░░] 45.2%         │
│    Theta   [█████░░░░░░░░░░░] 23.1%         │
│    Alpha   [███░░░░░░░░░░░░░] 12.8%         │
│    Beta    [████░░░░░░░░░░░░] 15.4%         │
│    Gamma   [██░░░░░░░░░░░░░░] 3.5%          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 4. BURST ACTIVITY FEED                      │
│    Burst #1 - 18:45:23.456                  │
│    Channels: CP3, C3, F5...                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 5. 🎤 AUDIO SYNC (LSL STREAM) ← NEW!        │
│    RMS: --  Peak: --                        │
│    Status: No audio stream detected         │
│    [Live waveform canvas - green line]      │
└─────────────────────────────────────────────┘
```

**If you still don't see panel #5**, the audio panel is at the very bottom - **scroll down!**

---

## ⚠️ Issue #2: How to Use Data with Grok

### Quick Answer: 3-Step Process

#### Step 1: Record Session (With Hardware)

```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate

# Meditation session
python scripts/run_mindmeld.py \
  --session "my_meditation" \
  --config config/meditation.yaml \
  --mode burst \
  --duration 300
```

**Creates files in**: `burst_data/my_meditation/`
- `burst_*.json.snappy` ← These are for Grok!

#### Step 2: Extract for Grok

```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate

# Extract all bursts from session
python extract_for_grok.py my_meditation --all > grok_input.json

# Or extract single burst
python extract_for_grok.py my_meditation --burst burst_20251111_180753_0001
```

**Output**: JSON ready to paste to Grok

#### Step 3: Analyze with Grok

1. Go to **https://grok.x.ai** or X.com (Grok tab)
2. Paste this prompt:

```
I recorded EEG brain activity during meditation using MW75 headphones.
Here's the data with synchronized audio. Please analyze:

1. What brain state am I in?
2. Which brain regions are most active?
3. Is there audio correlation with brain patterns?
4. Any recommendations for improvement?

[PASTE OUTPUT FROM extract_for_grok.py HERE]
```

3. Grok will tell you:
   - **Brain state**: "Relaxed (theta dominance)"
   - **Active regions**: "Frontal (F5, F6) - eye movement"
   - **Audio correlation**: "Breath sounds at 1.2s trigger alpha dip"
   - **Recommendations**: "Lower threshold to capture subtler states"

---

## 📊 Example: Complete Workflow

### Scenario: Analyze Your Meditation

```bash
# 1. Record 5-minute meditation
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate
python scripts/run_mindmeld.py --session meditation_001 --mode burst --duration 300

# Wait for session to complete...

# 2. Extract for Grok
python extract_for_grok.py meditation_001 --all

# Output will show:
# ================================================================================
# PASTE THE FOLLOWING TO GROK:
# ================================================================================
# {
#   "session_name": "meditation_001",
#   "total_bursts": 12,
#   "bursts": [...]
# }
```

**Copy the JSON output and paste to Grok with this prompt:**

```
I just completed a 5-minute meditation session.
I detected 12 bursts of heightened brain activity.

Each burst includes:
- 8-channel EEG (500Hz, 3 seconds)
- Synchronized microphone audio
- ML-computed band powers

Please analyze my meditation quality and progression.

[PASTE JSON HERE]
```

---

## 🎯 What Each File Contains

### Standard Burst Files (Created Automatically)

1. **`burst_*.npz`** - Raw EEG data (NumPy format)
   - For Python analysis
   - Load with: `data = np.load('burst_*.npz')`

2. **`burst_*_meta.json`** - Human-readable metadata
   - Timestamp, channels, metrics
   - View with: `cat burst_*_meta.json`

3. **`burst_*.json.snappy`** - Grok-ready export ← **USE THIS FOR GROK**
   - Snappy-compressed JSON
   - Contains: EEG + audio + ML insights
   - Extract with: `python extract_for_grok.py`

---

## 🔍 What Grok Can Tell You

### From Single Burst Analysis

**Input**: One 3-second burst
**Output**:
- **Brain state**: Relaxed / Alert / Focused / Drowsy
- **Dominant frequency**: "Theta (6Hz) - deep relaxation"
- **Channel activity**: "High F5/F6 - frontal thinking"
- **Anomaly score**: "0.15 - normal variability"
- **Audio correlation**: "Speech at 1.5s → beta spike"

### From Multi-Burst Session Analysis

**Input**: Full meditation session (multiple bursts)
**Output**:
- **Session quality**: "7/10 - Good meditation"
- **Progression**: "Started alert → relaxed by 3:24"
- **Best moment**: "Burst #4 (4:32) - deepest alpha"
- **Recommendations**: "Try lowering RMS threshold to 20µV"

---

## 💡 Pro Tips

### Tip 1: Use Tags in Config

```yaml
# config/meditation.yaml
tags: ["morning_meditation", "eyes_closed", "week_1"]
```

Grok prompt:
```
This is my first week practicing meditation (tag: week_1).
Compare to standard beginner patterns.
```

### Tip 2: Extract with Clipboard (Mac)

```bash
# Copy directly to clipboard
python extract_for_grok.py my_session --all | pbcopy

# Then Cmd+V in Grok chat
```

### Tip 3: Compare Sessions

```bash
# Extract two sessions
python extract_for_grok.py session_day1 --all > day1.json
python extract_for_grok.py session_day2 --all > day2.json

# Ask Grok:
# "Compare these two meditation sessions. Am I improving?"
# [PASTE day1.json]
# [PASTE day2.json]
```

---

## 🚨 Troubleshooting

### "No module named 'snappy'" Error

```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate  # ← IMPORTANT!
python extract_for_grok.py
```

Always activate venv first!

### "No audio stream detected" in UI

This is **EXPECTED** without hardware. The panel shows:
- ✅ Panel is visible (if you hard-refreshed)
- ⚠️ Status: "No audio stream detected" (normal without EEG hardware)
- ⚠️ Waveform: Empty (will show green line when hardware connects)

When you connect MW75 headphones + Neurable Research Kit:
- Status changes to: "🟢 Live"
- Waveform shows oscillating green line
- RMS/Peak values update 10x per second

### Audio Panel Still Not Visible After Hard Refresh

Check browser console (F12) for errors. Common issues:
- Browser cached old version (try different browser)
- JavaScript errors (check console)
- Scroll down - panel is at bottom!

---

## 📚 Complete Documentation

- **Full System Guide**: See `MINDMELD_SYSTEM_COMPLETE.md`
- **Grok Analysis Guide**: See `GROK_ANALYSIS_WORKFLOW.md`
- **Testing Results**: See `TEST_RESULTS.md`

---

## ✅ Quick Reference Card

### Extract for Grok (One-Liner)

```bash
cd ~/Downloads/eeg-burst-recorder && \
source venv/bin/activate && \
python extract_for_grok.py [SESSION_NAME] --all
```

### Best Grok Prompt

```
Analyze this EEG meditation session.
Tell me:
1. Brain state and quality
2. Progression over time
3. Recommendations for improvement

[PASTE JSON]
```

### Check Available Sessions

```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate
python extract_for_grok.py
```

---

**The MindMeld pipeline makes your brain data Grok-ready!** 🧠🤖

Hard refresh your browser to see the audio panel, then connect hardware to see it light up!
