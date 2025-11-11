# EEG Session Recording System - Live and Operational

## System Status: ✅ LIVE (UPDATED)

**Current Time**: 2025-11-11 14:42 PST
**Last Fix**: Session directory creation and absolute path handling

All core components are integrated and running with your live MW75 Neuro stream.

### Recent Fixes (2025-11-11 14:42)
- ✅ Fixed session directory creation (now created immediately on session start)
- ✅ Fixed data_dir to use absolute paths (prevents path resolution issues)
- ✅ Server restarted with fixes applied

## What's Working Right Now

### 1. Backend Server ✅
- **Running**: `http://localhost:8765` (PID 88851)
- **WebSocket**: `ws://localhost:8765/ws`
- **Status**: 1 client connected (your UI)
- **Real-time processing**: Burst detection + Spectral analysis

### 2. Web UI ✅
- **Location**: `~/Downloads/eeg-burst-recorder/ui/session_recorder_live.html`
- **Status**: Open in your browser
- **Connection**: Connected to WebSocket server
- **State**: Ready to start a session

### 3. Live Data Stream ✅
- **Source**: MW75 Neuro Neurable headphones
- **Channels**: 14 channels (Ch1-Ch14)
- **Sample Rate**: 500 Hz
- **Status**: Streaming continuously via LSL

### 4. Integrated Components ✅

**Burst Recorder**:
- Runs as subprocess when session starts
- Monitors stream for threshold violations
- Saves burst events as NPZ files
- Broadcasts burst events to UI via WebSocket

**Spectral Analyzer**:
- Runs in background thread during sessions
- Calculates band powers (Delta, Theta, Alpha, Beta, Gamma)
- Updates UI every 1 second
- Saves spectral data to CSV
- **Artifact-aware**: Excludes burst windows from analysis

## How to Use the System

### Starting a Session

1. **Open the UI** (already open):
   ```bash
   open ~/Downloads/eeg-burst-recorder/ui/session_recorder_live.html
   ```

2. **Configure your session** in the UI:
   - **Session Name**: e.g., "Deep Theta Training"
   - **Tags**: e.g., "meditation, theta, binaural-beats"
   - **Notes**: Any observations or goals
   - **Methods**:
     - ✅ Spectral Analysis (continuous FFT)
     - ✅ Burst Detection (event-triggered)
   - **Duration**: Leave blank for continuous, or set minutes
   - **Thresholds**:
     - RMS: 50.0 µV (default)
     - P2P: 100.0 µV (default)

3. **Click "Start Recording"**

### What Happens During Recording

**Real-time UI Updates**:

```
╔══════════════════════════════════════════════════╗
║  Session: Deep Theta Training                   ║
║  Time: 00:05:32        Bursts: 3                ║
╠══════════════════════════════════════════════════╣
║  Spectral Bands:                                 ║
║    Delta:  ████████ 68% ↑ High                  ║
║    Theta:  ████████████ 82% ↑ Very High         ║
║    Alpha:  ████ 35% → Stable                    ║
║    Beta:   ██ 18% ↘ Low                         ║
║    Gamma:  █ 12% ↘ Very Low                     ║
║                                                  ║
║  Recent Bursts:                                  ║
║    • 00:05:17 - Eye Blink (Ch1, Ch6)            ║
║    • 00:04:32 - Movement (Ch1, Ch3, Ch6)        ║
║    • 00:03:48 - Jaw Clench (Ch7, Ch8)           ║
║                                                  ║
║  Quality: 92% Good                              ║
║  Signal: 87%  Artifacts: 25%  Integrity: 99%   ║
╚══════════════════════════════════════════════════╝
```

**Behind the Scenes**:
- Burst recorder subprocess monitors stream
- Spectral analyzer calculates FFT every 1 second
- WebSocket broadcasts updates to UI
- All data saved to `burst_data/{session_id}/`

### Stopping a Session

1. **Click "Stop Recording"** in UI

2. **System finalizes**:
   - Stops burst recorder subprocess
   - Stops spectral analyzer thread
   - Saves session metadata
   - Closes CSV files

3. **Data saved to**:
   ```
   burst_data/{session_id}/
   ├── session.json           # Session metadata
   ├── spectral_data.csv      # Continuous band powers
   └── bursts/
       ├── burst_0001.npz     # Burst waveform data
       ├── burst_0001_meta.json
       ├── burst_0002.npz
       └── ...
   ```

## Technical Architecture

### Data Flow

```
MW75 Neuro Headphones (LSL Stream)
         │
         ├─────────────┬─────────────┐
         │             │             │
    Burst Monitor   Spectral    Session
    (subprocess)    Analyzer    Server
         │          (thread)    (aiohttp)
         │             │             │
         └─────────────┴─────────────┤
                                     │
                              WebSocket
                                     │
                                 Web UI
                              (real-time)
```

### Component Integration

**Session Server** (`server/session_server.py`):
- WebSocket + REST API server
- Manages session lifecycle
- Coordinates burst recorder and spectral analyzer
- Broadcasts real-time data to connected clients

**Burst Recorder** (`burst_recorder.py`):
- Runs as subprocess during sessions
- Monitors LSL stream for threshold violations
- Saves burst events as NPZ files + JSON metadata
- Sends LSL markers for each burst

**Spectral Analyzer** (`server/spectral_analyzer.py`):
- Runs as background thread during sessions
- Continuous FFT analysis (2-second windows, 50% overlap)
- Calculates 5 frequency bands every 1 second
- **Artifact-aware**: Uses burst timestamps to exclude contaminated windows
- Saves spectral data to CSV

**Web UI** (`ui/session_recorder_live.html`):
- Connects to WebSocket server
- Real-time display of spectral bands and burst events
- Session controls (start/stop)
- Auto-reconnection on disconnect

## File Locations

```
eeg-burst-recorder/
├── server/
│   ├── session_server.py          ✅ Running (PID 88851)
│   ├── spectral_analyzer.py       ✅ Tested and working
│   ├── requirements.txt            ✅ Installed
│   └── test_spectral.csv           ✅ Test output
│
├── ui/
│   └── session_recorder_live.html  ✅ Open in browser
│
├── burst_recorder.py               ✅ Integrated
├── analyze_burst.py                ✅ Working
│
├── burst_data/                     📁 Session storage
│   └── {session_id}/
│       ├── session.json
│       ├── spectral_data.csv
│       └── bursts/
│
└── venv/                           ✅ Activated
```

## API Endpoints

**REST API**:
```bash
# Check server status
curl http://localhost:8765/api/status

# Start a session
curl -X POST http://localhost:8765/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Session",
    "tags": ["meditation", "theta"],
    "notes": "Testing the system",
    "methods": ["spectral", "burst"],
    "duration": 300,
    "threshold_rms": 50.0,
    "threshold_p2p": 100.0
  }'

# Stop the current session
curl -X POST http://localhost:8765/api/sessions/stop

# List all sessions
curl http://localhost:8765/api/sessions

# Health check
curl http://localhost:8765/health
```

**WebSocket Messages**:

Server → Client:
```javascript
{
  type: 'burst_detected',
  burst_id: 'burst_0001',
  timestamp: '2025-11-11T14:35:22.123Z',
  time_seconds: 12.5,
  channels: ['Ch1', 'Ch3', 'Ch6'],
  metrics: { ... }
}

{
  type: 'spectral_update',
  timestamp: '2025-11-11T14:35:23.456Z',
  time_seconds: 13.0,
  bands: {
    delta: 68.0,
    theta: 82.0,
    alpha: 35.0,
    beta: 18.0,
    gamma: 12.0
  },
  quality: {
    signal_quality: 92.0,
    artifact_level: 25.0
  },
  is_artifact: false
}

{
  type: 'session_started',
  session: { id: '20251111_143522', name: 'My Session', ... }
}

{
  type: 'session_stopped',
  session: { id: '20251111_143522', duration_seconds: 300, ... }
}
```

Client → Server:
```javascript
{
  type: 'ping'  // Get 'pong' response
}

{
  type: 'request_status'  // Get current status
}
```

## Comparison: Before vs. Now

### Previous System (Meditation Analysis)
- ❌ No real-time UI
- ❌ Manual script execution
- ❌ Artifacts contaminated spectral data
- ✅ Spectral analysis (offline)

### Current System
- ✅ Real-time web UI
- ✅ Session management
- ✅ Live burst detection
- ✅ Live spectral analysis
- ✅ **Artifact-aware spectral processing**
- ✅ WebSocket streaming
- ✅ Automatic data saving

## Next Steps (Optional Enhancements)

### Short-term (Days)
- [ ] Session review page (browse historical sessions)
- [ ] Export to EDF format (clinical standard)
- [ ] PDF report generation
- [ ] Burst classification (blinks, movements, jaw clenches)

### Medium-term (Weeks)
- [ ] SQLite database for session metadata
- [ ] Multi-session comparison view
- [ ] Real-time frequency-domain visualization (spectrograms)
- [ ] Mobile-responsive UI improvements

### Long-term (Months)
- [ ] Machine learning burst classifier
- [ ] Cloud storage integration
- [ ] Multi-user support
- [ ] Advanced analytics (coherence, connectivity)

## Testing the System

### Quick Test (5 minutes)

1. **UI is already open** ✅

2. **Start a 60-second test session**:
   - Name: "System Test"
   - Tags: "test"
   - Duration: 1 minute
   - Both methods enabled
   - Click "Start Recording"

3. **Observe**:
   - Timer counting up
   - Spectral bands updating every second
   - Bursts appearing in feed (if you move your head)
   - Quality metrics

4. **Stop session** after 60 seconds

5. **Check saved data**:
   ```bash
   ls -lh ~/Downloads/eeg-burst-recorder/burst_data/
   ```

### Full Test (30 minutes)

1. **Meditation session**:
   - Name: "Deep Theta Training"
   - Tags: "meditation, theta"
   - Duration: 20 minutes
   - Notes: "Binaural beats at 432Hz"

2. **During session**:
   - Minimize movements (reduce bursts)
   - Monitor theta band (should increase)
   - Watch for artifact bursts (blinks, swallows)

3. **After session**:
   - Review CSV: `burst_data/{session_id}/spectral_data.csv`
   - Analyze bursts: `python analyze_burst.py burst_data/{session_id}/bursts/burst_0001.npz`
   - Compare to previous meditation data

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :8765

# Kill existing process
kill -9 {PID}

# Restart server
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate
python server/session_server.py
```

### UI shows "Disconnected"
```bash
# Check server is running
curl http://localhost:8765/health

# Check WebSocket endpoint
wscat -c ws://localhost:8765/ws

# Refresh browser
# Check browser console for errors
```

### No spectral updates
- Verify LSL stream is active
- Check burst_recorder is running: `ps aux | grep burst_recorder`
- Look for errors in server terminal
- Ensure MW75 headphones are connected

### Bursts not detected
- Lower thresholds (try RMS: 30.0, P2P: 60.0)
- Check LSL stream amplitude: `python burst_recorder.py --duration 5`
- Move your head/jaw to trigger bursts

## Support

**Documentation**:
- `README.md` - System overview
- `QUICKSTART.md` - Quick setup guide
- `SYSTEM_GUIDE.md` - Operational details
- `ANALYSIS_COMPARISON.md` - Method comparison
- `SESSION_UI_DESIGN.md` - UI/UX specifications
- `TEST_RESULTS.md` - Test data and validation

**Logs**:
- Server: Terminal running `session_server.py`
- Browser: DevTools Console (F12)
- Files: `burst_data/{session_id}/`

---

**Status**: ✅ System operational and ready for sessions

**Your Turn**: Start a session in the UI and watch your brain activity in real-time!
