# MindMeld Pipeline - Quick Start Guide

**Your Step-by-Step Guide to Recording Your First Session**

---

## 🚦 BEFORE YOU START - Prerequisites Checklist

Check these off BEFORE running anything:

- [ ] **Neurable Research Kit app is OPEN** (look in Applications folder)
- [ ] **MW75 headphones are ON and PAIRED** to your Mac
- [ ] **You see "Streaming" or data flowing** in the Neurable app
- [ ] **Headphones are on your head** (at least for testing)

**Can't find the Neurable app?**
- Look in Applications folder for "Neurable Research Kit EEG Visualizer"
- If not installed, the installer is in ~/Downloads/

**Headphones not streaming?**
- Turn them on
- Pair via Bluetooth
- Open Neurable app and click "Start Streaming"

---

## 📍 WHERE TO RUN COMMANDS

**Open Terminal** and run:

```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate
```

You should see `(venv)` appear at the start of your prompt. This means you're ready.

---

## 🎯 OPTION 1: Quick 30-Second Test (RECOMMENDED FIRST)

**What this does:**
- Runs for 30 seconds
- Detects any EEG bursts above threshold
- Saves data to `burst_data/quick_test/`
- You can just sit there, blink, or think - any activity might trigger bursts

**Command:**
```bash
python scripts/run_mindmeld.py --session quick_test --mode burst --duration 30
```

**What you'll see:**

1. **First (2-5 seconds):**
   ```
   ============================================================
   🧠 MindMeld EEG-Grok Pipeline
   ============================================================
   Session: quick_test
   Mode: burst
   Config: config/meditation.yaml
   Audio: Enabled
   Output: burst_data/quick_test
   ============================================================

   Connecting to LSL stream...
   ```

2. **If it finds the stream (good!):**
   ```
   ✓ Connected to EEG stream
   ✓ Channels: CP3, C3, F5, PO3, PO4, F6, C4, CP4
   ✓ Sample rate: 500.0 Hz
   ✓ Event marker outlet created
   ✓ Audio sync initialized

   🎯 Monitoring for bursts (RMS > 25.0µV, P2P > 50.0µV)
   Press Ctrl+C to stop...
   ```

3. **While running:**
   - You might see: `🔥 Burst detected! Channel: C3 (RMS: 62.3µV)`
   - Or you might see nothing (that's okay! It means no bursts exceeded threshold)
   - You'll see a countdown or nothing at all - both are normal

4. **After 30 seconds:**
   ```
   ✓ MindMeld session ended

   ============================================================
   📊 Session Complete
   ============================================================
   Data saved to: burst_data/quick_test/
   Bursts/chunks: 3

   💡 To analyze with Grok:
      1. Decompress any .json.snappy file:
         python -c "import snappy; print(snappy.uncompress(open('burst_data/quick_test/burst_*.json.snappy','rb').read()).decode())"
      2. Paste the JSON output to Grok for analysis
      3. Ask Grok: 'Analyze this EEG session for meditation patterns'
   ============================================================
   ```

---

## ✅ HOW TO KNOW IT WORKED

**Check if files were created:**
```bash
ls -lh burst_data/quick_test/
```

**You should see files like:**
- `burst_20251111_123456_0001.npz` (EEG data)
- `burst_20251111_123456_0001_meta.json` (readable metadata)
- `burst_20251111_123456_0001.json.snappy` (Grok export)

**If you see 0 bursts:**
- This is NORMAL! It means your brain was calm
- Lower the threshold to catch more subtle activity:
  ```bash
  python burst_recorder.py --threshold-rms 15 --threshold-p2p 30 --duration 30
  ```

**If you see "No EEG stream found":**
- Check Neurable Research Kit is running
- Verify headphones are streaming (look for live data in Neurable app)
- Try waiting 10 seconds and run again

---

## 🎯 OPTION 2: Meditation Mode (5 Minutes)

**What this does:**
- Runs for 5 minutes
- Designed for calm meditation states
- Uses sensitive thresholds (catches subtle alpha/theta waves)
- Good for: meditation, relaxation, eyes-closed resting

**Command:**
```bash
python scripts/run_mindmeld.py --session meditation_01 --mode burst --duration 300
```

**What to do:**
1. Put on headphones
2. Sit comfortably
3. Close your eyes or meditate
4. Let it run for 5 minutes
5. Press Ctrl+C if you want to stop early

**Expected bursts:**
- You might see 5-20 bursts during meditation
- Theta/alpha bands often trigger in calm states
- Eye blinks cause frontal bursts (F5, F6 channels)

---

## 🎯 OPTION 3: Conversation Mode (Continuous Recording)

**What this does:**
- Records 30-second chunks continuously
- Doesn't wait for bursts - captures EVERYTHING
- Good for: talking, podcasts, voice conversations
- Saves a chunk every 30 seconds

**Command:**
```bash
python scripts/run_mindmeld.py --session grok_convo --mode continuous --duration 180
```

**What to do:**
1. Put on headphones
2. Talk out loud (or have a conversation)
3. System records 30-second chunks automatically
4. Good for correlating speech with brain activity

**Expected output:**
- Saves a chunk every 30 seconds
- After 180 seconds (3 minutes) you'll have 6 chunks
- Each chunk has EEG + audio + ML insights

---

## 🛑 HOW TO STOP EARLY

**Press `Ctrl+C` at any time**

You'll see:
```
^C
✓ MindMeld session ended
```

All data up to that point is saved safely.

---

## 📊 WHAT TO DO WITH THE DATA

### View a Burst in Human-Readable Format

```bash
cat burst_data/quick_test/burst_*_meta.json | head -30
```

You'll see:
```json
{
  "burst_id": "burst_20251111_123456_0001",
  "sample_rate": 500.0,
  "n_samples": 1500,
  "channel_names": ["CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4"],
  "timestamp": "2025-01-11T12:34:56.789",
  "channels": [
    {
      "channel": "C3",
      "rms": 62.3,
      "p2p": 145.7
    }
  ]
}
```

### Decompress a Grok Export (See ML Insights)

```bash
cd burst_data/quick_test
python -c "import snappy; print(snappy.uncompress(open('$(ls burst_*.json.snappy | head -1)','rb').read()).decode())" | head -50
```

You'll see:
```json
{
  "burst_id": "burst_20251111_123456_0001",
  "eeg": {
    "data": [[...], [...]],
    "sample_rate": 500.0,
    "channels": ["CP3", "C3", ...],
    "metrics": {"C3": {"rms": 62.3, "p2p": 145.7}}
  },
  "audio": {
    "data": [...],
    "start_ts": 1699726598000,
    "duration": 3.0,
    "lsl_offset_ms": 8.4
  },
  "insights": {
    "dominant_band": "theta",
    "powers": {
      "delta": 51.26,
      "theta": 15.24,
      "alpha": 4.65,
      "beta": 10.05,
      "gamma": 14.72
    },
    "anomaly_score": 0.15,
    "state": "relax"
  }
}
```

**Key insights:**
- `dominant_band`: Which frequency band is strongest (delta/theta/alpha/beta/gamma)
- `state`: relax (calm), alert (active), or neutral
- `anomaly_score`: 0.0-1.0, higher = more unusual activity

---

## 🔧 TROUBLESHOOTING

### "No LSL stream found"
- **Fix**: Make sure Neurable Research Kit is running AND streaming
- Check the app shows live EEG data
- Wait 5-10 seconds after starting the app, then try again

### "Audio sync failed" or audio errors
- **Not critical!** EEG will still record
- To disable audio: add `--no-audio` flag
  ```bash
  python scripts/run_mindmeld.py --session test --no-audio
  ```

### No bursts detected
- **This is normal!** Lower the threshold:
  ```bash
  python burst_recorder.py --threshold-rms 15 --threshold-p2p 30
  ```
- Or try: blink rapidly, clench jaw, or move your head

### Too many bursts (hundreds)
- Increase threshold:
  ```bash
  python burst_recorder.py --threshold-rms 50 --threshold-p2p 100
  ```

---

## 🎓 UNDERSTANDING THE OUTPUT

### File Types

1. **`.npz` files** - EEG data (for Python analysis)
   - Load with: `np.load('burst_*.npz')`
   - Contains raw EEG samples

2. **`_meta.json` files** - Human-readable metadata
   - Open with any text editor
   - Shows which channels triggered, timestamps, thresholds

3. **`.json.snappy` files** - Grok-ready exports
   - Compressed for efficiency
   - Includes EEG + audio + ML insights
   - Decompress and paste to Grok for AI analysis

### Brain States

- **relax** - Theta/alpha dominant (meditation, calm)
- **alert** - Beta/gamma dominant (focused, active thinking)
- **neutral** - Delta dominant or mixed (baseline)

### Frequency Bands

- **Delta (0.5-4 Hz)** - Deep sleep, unconscious
- **Theta (4-8 Hz)** - Meditation, light sleep, creativity
- **Alpha (8-13 Hz)** - Relaxed awareness, eyes closed
- **Beta (13-30 Hz)** - Active thinking, focus, anxiety
- **Gamma (30-100 Hz)** - Peak concentration, problem solving

---

## 📝 QUICK REFERENCE COMMANDS

**30-second test:**
```bash
python scripts/run_mindmeld.py --session test --duration 30
```

**5-minute meditation:**
```bash
python scripts/run_mindmeld.py --session meditation --duration 300
```

**Conversation mode (3 minutes):**
```bash
python scripts/run_mindmeld.py --session talk --mode continuous --duration 180
```

**Without audio:**
```bash
python scripts/run_mindmeld.py --session test --no-audio
```

**Check what you recorded:**
```bash
ls -lh burst_data/YOUR_SESSION_NAME/
```

---

## ✨ TIPS FOR BEST RESULTS

1. **Start with 30 seconds** to verify everything works
2. **Ensure good contact** - adjust headphones for clean signal
3. **Minimize artifacts** - avoid excessive movement, jaw clenching
4. **Try different states** - compare meditation vs active thinking
5. **Use descriptive session names** - helps organize data later
   - Good: `meditation_morning_01`, `podcast_chat_01`
   - Bad: `test`, `session`, `data`

---

**Ready? Start with the 30-second test above! 🚀**
