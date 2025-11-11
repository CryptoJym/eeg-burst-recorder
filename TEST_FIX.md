# Session Recording System - Test After Fixes

## Problem Identified and Fixed (2025-11-11 14:42)

### What Was Wrong
1. **Session directory not created**: Directory was only created when STOPPING a session (in `save_session()`), but burst recorder and spectral analyzer needed it to exist BEFORE starting
2. **Relative path issues**: `data_dir` was using relative path `'../burst_data'` which could cause issues depending on where the server was run from

### What Was Fixed
1. **Immediate directory creation**: Session directory is now created in `start_session()` BEFORE starting monitors
2. **Absolute paths**: `data_dir` now uses `.resolve()` to convert to absolute path immediately

## Testing the Fix

### 1. Verify Server is Running
```bash
curl http://localhost:8765/health
# Should return: {"status": "healthy"}
```

### 2. Open the UI
The UI should already be open in your browser at:
```
file:///Users/jamesbrady/Downloads/eeg-burst-recorder/ui/session_recorder_live.html
```

If not, open it now. You should see "Connected" status in green.

### 3. Start a New Test Session

In the UI:
1. **Session Name**: "Path Fix Test"
2. **Tags**: "test, fix-verification"
3. **Notes**: "Testing session directory creation fix"
4. **Methods**: Both checkboxes enabled (Spectral + Burst)
5. **Duration**: 30 seconds
6. **Thresholds**: Default (RMS: 50.0, P2P: 100.0)

Click **"Start Recording"**

### 4. What You Should See in the UI

**During the 30-second session:**
- Timer counting up
- Spectral bands updating every 1-2 seconds showing percentages:
  - Delta, Theta, Alpha, Beta, Gamma bands
- Burst events appearing when you move (blink, jaw clench, head movement)
- Quality metrics updating

**Console output (if you check server logs):**
```bash
INFO:__main__:Starting session: 20251111_XXXXXX
INFO:__main__:Created session directory: /Users/jamesbrady/Downloads/eeg-burst-recorder/burst_data/20251111_XXXXXX
INFO:__main__:Burst recorder started: PID XXXXX
INFO:spectral_analyzer:✓ Found stream: MW75 Neuro Neurable Stream
INFO:spectral_analyzer:Writing spectral data to: /Users/jamesbrady/Downloads/eeg-burst-recorder/burst_data/20251111_XXXXXX/spectral_data.csv
INFO:__main__:Spectral analyzer connected to stream
```

**KEY INDICATORS OF SUCCESS:**
- ✅ "Created session directory" log message with ABSOLUTE PATH
- ✅ Spectral data CSV path shows ABSOLUTE PATH (not "../")
- ✅ UI shows real-time updates every second

### 5. After Session Completes (30 seconds)

Click **"Stop Recording"** if it didn't auto-stop.

### 6. Verify Data Was Saved

```bash
# Find the latest session directory
ls -lth ~/Downloads/eeg-burst-recorder/burst_data/ | head -5

# Check session contents (replace XXXXXX with your session ID)
ls -lh ~/Downloads/eeg-burst-recorder/burst_data/20251111_XXXXXX/

# You should see:
# - session.json (session metadata)
# - spectral_data.csv (continuous spectral analysis)
# - bursts/ directory (if any bursts were detected)
```

**Expected files:**
```
burst_data/20251111_XXXXXX/
├── session.json           # Session metadata
├── spectral_data.csv      # Spectral band powers (1 row per second)
└── bursts/               # Burst events (if detected)
    ├── burst_0001.npz
    ├── burst_0001_meta.json
    └── ...
```

### 7. Verify CSV Content

```bash
# Check spectral data (replace XXXXXX with session ID)
head ~/Downloads/eeg-burst-recorder/burst_data/20251111_XXXXXX/spectral_data.csv
```

**Expected output:**
```csv
timestamp,time_seconds,delta_power,theta_power,alpha_power,beta_power,gamma_power,signal_quality,artifact_level
2025-11-11T14:XX:XX.XXXXXX,2.026,91.38,2.02,0.95,0.72,4.92,0.0,8.4
2025-11-11T14:XX:XX.XXXXXX,3.025,87.23,2.29,0.98,0.91,8.59,0.0,14.9
...
```

## Success Criteria

✅ **PASS if:**
1. Session directory created immediately (before data processing starts)
2. All paths in logs are ABSOLUTE (start with `/Users/jamesbrady/...`)
3. UI shows real-time spectral updates every 1-2 seconds
4. CSV file exists with spectral data
5. session.json exists with metadata

❌ **FAIL if:**
1. "No such file or directory" errors
2. Logs show relative paths (`../burst_data/...`)
3. UI shows "Disconnected" or no updates
4. No files saved after session

## Troubleshooting

### UI shows "Disconnected"
```bash
# Refresh the browser page
# Check server is running:
curl http://localhost:8765/health
```

### No spectral updates in UI
- Check browser console (F12) for JavaScript errors
- Verify MW75 headphones are connected and streaming
- Check server logs for errors

### Session directory not created
This was the original bug - should be fixed now. If still happening:
```bash
# Check server logs for errors:
tail -50 ~/.../server_logs
```

## Next Steps After Successful Test

Once verified working:
1. Try longer sessions (5-10 minutes)
2. Test meditation sessions with binaural beats
3. Compare spectral data to previous meditation analysis
4. Experiment with different threshold values

---

**Test Status**: Ready to test
**Server Status**: Running at http://localhost:8765
**UI Location**: file:///Users/jamesbrady/Downloads/eeg-burst-recorder/ui/session_recorder_live.html
