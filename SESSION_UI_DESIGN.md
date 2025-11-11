# Session Recording UI/UX Design

## Overview

A comprehensive interface for managing EEG recording sessions that integrates both spectral analysis and burst detection capabilities.

---

## Design Philosophy

### Core Principles

1. **Clarity**: User always knows recording status
2. **Control**: Easy start/stop, clear feedback
3. **Insight**: Real-time metrics without overwhelming
4. **Flexibility**: Choose analysis methods per session
5. **Traceability**: Every session has metadata and context

### User Flows

```
┌─────────────────────────────────────────────────┐
│ Primary Flow: Record a Session                  │
├─────────────────────────────────────────────────┤
│ 1. Configure session (name, tags, methods)     │
│ 2. Review threshold settings                   │
│ 3. Start recording                             │
│ 4. Monitor real-time metrics                   │
│ 5. Stop recording                              │
│ 6. Review/export results                       │
└─────────────────────────────────────────────────┘
```

---

## Main Interface Layout

### Top Bar: Status & Control

```
┌────────────────────────────────────────────────────────────────┐
│  🎧 EEG Session Recorder                        [Settings] [?] │
├────────────────────────────────────────────────────────────────┤
│  Stream: MW75 Neuro Neurable (500 Hz, 14 channels)      🟢 LIVE│
│  Recording: [●] 00:15:32           Bursts: 12    Storage: 2.3MB│
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- **Stream indicator**: Shows connected device and quality (green/yellow/red)
- **Recording timer**: Elapsed time with red dot when active
- **Burst counter**: Real-time count of detected bursts
- **Storage meter**: Current session data size

### Center: Session Configuration Panel

```
┌────────────────────────────────────────────────────────────────┐
│  Session Setup                                                  │
├────────────────────────────────────────────────────────────────┤
│  Session Name: [Meditation Session 2025-11-11                ] │
│                                                                 │
│  Tags: [meditation] [theta-training] [+]                       │
│                                                                 │
│  Notes: [Trying 20-min session with binaural beats           ] │
│         [                                                     ] │
│                                                                 │
│  Analysis Methods:                                              │
│  ☑ Spectral Analysis (Delta, Theta, Alpha, Beta, Gamma)       │
│  ☑ Burst Detection   (Artifacts + Events)                      │
│  ☐ Heart Rate Variability (if available)                       │
│                                                                 │
│  Duration: ○ Continuous  ● Timed: [20] minutes                 │
│                                                                 │
│            [ Configure Advanced Settings... ]                   │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- **Session name**: Auto-generated or custom
- **Tags**: Clickable pills for categorization (meditation, focus, sleep, etc.)
- **Notes**: Free-form text for context
- **Analysis toggles**: Choose which methods to run
- **Duration**: Continuous or timed recording
- **Advanced settings**: Threshold tuning, output location

### Center: Real-Time Monitoring (During Recording)

```
┌────────────────────────────────────────────────────────────────┐
│  Live Metrics                                  Session: 00:15:32│
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🧠 Spectral Bands                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Delta (0.5-4 Hz)    ████████░░░░  68%  ↗ Increasing     │  │
│  │ Theta (4-8 Hz)      ██████████░░  82%  ↑ High           │  │
│  │ Alpha (8-13 Hz)     ████░░░░░░░░  35%  ↘ Decreasing     │  │
│  │ Beta (13-30 Hz)     ██░░░░░░░░░░  18%  → Stable         │  │
│  │ Gamma (30-100 Hz)   █░░░░░░░░░░░  12%  → Stable         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ⚡ Burst Activity                                Last: 00:00:45│
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Total Bursts: 12                                         │  │
│  │                                                           │  │
│  │ Recent Events:                                           │  │
│  │ • 00:15:17 - Ch1, Ch6 (RMS: 1842 µV)  [Eye Blink]       │  │
│  │ • 00:14:32 - Ch1, Ch3, Ch6 (RMS: 2103 µV)  [Movement]   │  │
│  │ • 00:13:48 - Ch7, Ch8 (RMS: 987 µV)  [Jaw Clench]       │  │
│  │                                                           │  │
│  │ Burst Rate: 0.8/min  (normal)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  📊 Session Quality                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Signal Quality:  ███████████░  92%  Good                 │  │
│  │ Artifact Level:  ███░░░░░░░░░  25%  Low                  │  │
│  │ Data Integrity:  ████████████  99%  Excellent            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│                        [■ STOP RECORDING]                       │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- **Spectral bands**: Live percentage bars with trend indicators
- **Burst activity**: Recent events with auto-classification
- **Session quality**: Overall health metrics
- **Stop button**: Large, obvious control

### Bottom: Session History

```
┌────────────────────────────────────────────────────────────────┐
│  Recent Sessions                                    [View All] │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 🧘 Meditation Session 2025-11-11       20:15  [View]    │  │
│  │    Duration: 20:00    Bursts: 8    Theta peak: 29.5min  │  │
│  │    Tags: meditation, theta-training                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 🎯 Focus Work Session                  15:42  [View]    │  │
│  │    Duration: 45:30    Bursts: 23   Beta peak: 12.3min   │  │
│  │    Tags: focus, work, pomodoro                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 😴 Sleep Session                       23:15  [View]    │  │
│  │    Duration: 6:30:00  Bursts: 142  Delta dominant       │  │
│  │    Tags: sleep, recovery                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- **Session cards**: Previous recordings with key metrics
- **Quick access**: One-click to view detailed results
- **At-a-glance**: Icon, time, duration, highlights

---

## Advanced Settings Panel

```
┌────────────────────────────────────────────────────────────────┐
│  Advanced Recording Settings                         [✕ Close] │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⚡ Burst Detection Thresholds                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ RMS Threshold:     [50] µV     │ Less ◄─────●─────► More │  │
│  │ P2P Threshold:     [100] µV    │ Less ◄─────●─────► More │  │
│  │                                                           │  │
│  │ Sensitivity: Medium                                       │  │
│  │ • Low (RMS: 100, P2P: 200)   - Major events only         │  │
│  │ ● Medium (RMS: 50, P2P: 100) - Balanced (recommended)    │  │
│  │ • High (RMS: 30, P2P: 60)    - Catch small bursts        │  │
│  │ • Custom                      - Manual adjustment         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  📊 Spectral Analysis Settings                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Window Size: [2] seconds   Overlap: [50]%                │  │
│  │ Bands: ☑ Delta ☑ Theta ☑ Alpha ☑ Beta ☑ Gamma          │  │
│  │ Update Rate: [1] second                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  🎯 Burst Window Configuration                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Pre-burst:  [1.0] seconds  (context before event)        │  │
│  │ Post-burst: [2.0] seconds  (event decay capture)         │  │
│  │ Cooldown:   [3.0] seconds  (minimum time between bursts) │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  💾 Output Settings                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Output Directory: [~/Documents/eeg-sessions/            ] │  │
│  │                                                           │  │
│  │ Save Format:                                              │  │
│  │ ☑ NPZ (NumPy arrays - for analysis)                      │  │
│  │ ☑ JSON (Metadata - human-readable)                       │  │
│  │ ☐ CSV (Spectral bands - spreadsheet-friendly)            │  │
│  │ ☐ EDF (European Data Format - clinical standard)         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│                        [Cancel]  [Save Settings]                │
└────────────────────────────────────────────────────────────────┘
```

---

## Session Review Screen

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back to Sessions                                            │
├────────────────────────────────────────────────────────────────┤
│  🧘 Meditation Session 2025-11-11                              │
│  November 11, 2025 • 20:15 - 20:35 • Duration: 20:00           │
│                                                                 │
│  Tags: meditation, theta-training, binaural-beats              │
│  Notes: 20-min session with 7Hz binaural beats. Felt very      │
│         focused from minute 10 onwards.                         │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  📊 Spectral Analysis Summary                                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Graph: Frequency bands over time - interactive chart]        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Power                                                     │  │
│  │   ↑                                                       │  │
│  │   │    ╱╲                                                 │  │
│  │   │   ╱  ╲    Theta ━━━                                  │  │
│  │   │  ╱    ╲╲╱╲    ╱╲                                      │  │
│  │   │ ╱      ╲  ╲  ╱  ╲                                     │  │
│  │   │╱        ╲  ╲╱    ╲  Alpha ──────                     │  │
│  │   └─────────────────────────────────────────────────────→│  │
│  │     0        5       10      15      20        Time (min) │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Key Moments:                                                   │
│  • 00:02:30 - Alpha rise (relaxation onset)                    │
│  • 00:10:15 - Theta peak (deep meditation entry)               │
│  • 00:18:45 - Theta sustained (peak state maintained)          │
│                                                                 │
│  Average Band Powers:                                           │
│  Delta: 45%  Theta: 68%  Alpha: 32%  Beta: 12%  Gamma: 8%     │
│                                                                 │
│  [Export Spectral Data (CSV)]                                  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  ⚡ Burst Events (8 total)                                      │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 00:00:12 - Eye Blink        Ch1, Ch6  [View Waveform]   │  │
│  │            RMS: 1245 µV, P2P: 3840 µV                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 00:02:45 - Movement         Ch1, Ch3, Ch6  [View]       │  │
│  │            RMS: 1890 µV, P2P: 4923 µV                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 00:04:18 - Jaw Clench       Ch7, Ch8  [View]            │  │
│  │            RMS: 987 µV, P2P: 2341 µV                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ...                                                            │
│                                                                 │
│  Artifact Analysis:                                             │
│  • 6 artifacts detected (75% of bursts)                        │
│  • Clean windows: 92% of session                               │
│  • Recommendation: Exclude bursts from spectral analysis       │
│                                                                 │
│  [Export Burst Data (NPZ + JSON)]  [Generate Clean CSV]        │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  Actions                                                        │
├────────────────────────────────────────────────────────────────┤
│  [📥 Export Session]  [📊 Advanced Analysis]  [🗑️ Delete]     │
│                                                                 │
│  Export Options:                                                │
│  • Full dataset (all channels, all methods)                    │
│  • Cleaned dataset (artifacts removed)                         │
│  • Summary report (PDF)                                        │
│  • Research package (EDF + metadata)                           │
└────────────────────────────────────────────────────────────────┘
```

---

## Interaction Patterns

### Recording Start Sequence

```
1. User clicks "Start Recording"
   ↓
2. System checks:
   ✓ LSL stream available?
   ✓ Output directory writable?
   ✓ Sufficient disk space?
   ↓
3. If checks pass:
   • Session metadata created
   • Timer starts
   • Monitoring panels activate
   • Real-time metrics begin updating
   ↓
4. Visual feedback:
   • Red recording dot pulsing
   • Timer incrementing
   • Metrics populating
```

### Burst Detection Visual

```
When burst detected:
1. Flash alert in burst panel
2. Increment burst counter
3. Add event to recent list
4. Send notification (optional):
   ┌──────────────────────────────┐
   │ 🔴 Burst Detected            │
   │ Ch1, Ch6 - Eye blink         │
   │ RMS: 1845 µV                 │
   └──────────────────────────────┘
```

### Quality Warnings

```
If signal quality drops:
┌────────────────────────────────────────┐
│ ⚠️ Signal Quality Warning               │
│                                        │
│ Ch3, Ch5 signal weak                   │
│                                        │
│ Possible causes:                       │
│ • Poor electrode contact               │
│ • Headphone adjustment needed          │
│ • Battery low                          │
│                                        │
│ [Dismiss]  [Check Troubleshooting]    │
└────────────────────────────────────────┘
```

---

## Mobile Responsive Layout

### Compact View (Phone)

```
┌─────────────────────┐
│ 🎧 EEG Recorder     │
├─────────────────────┤
│ 🟢 MW75 Connected   │
│ ● 00:15:32          │
│ 12 bursts  2.3 MB   │
├─────────────────────┤
│ Session: Meditation │
│                     │
│ 🧠 Bands            │
│ Theta ████████ 82%  │
│ Alpha ████ 35%      │
│ Beta  ██ 18%        │
│                     │
│ ⚡ Recent Bursts    │
│ • 00:15:17 Blink    │
│ • 00:14:32 Move     │
│                     │
│  [■ STOP]           │
└─────────────────────┘
```

---

## Color Scheme

### Status Colors

- **Live/Active**: `#00C851` (Green)
- **Recording**: `#FF4444` (Red)
- **Warning**: `#FFBB33` (Amber)
- **Error**: `#CC0000` (Dark Red)
- **Neutral**: `#33B5E5` (Blue)

### Band Colors

- **Delta**: `#9933FF` (Purple)
- **Theta**: `#00C851` (Green)
- **Alpha**: `#33B5E5` (Blue)
- **Beta**: `#FFBB33` (Orange)
- **Gamma**: `#FF4444` (Red)

---

## Accessibility Features

### Screen Reader Support

- All status changes announced
- Button labels clear and descriptive
- Real-time metrics with ARIA live regions

### Keyboard Navigation

```
Spacebar: Start/Stop recording
T: Toggle spectral/burst view
E: Export current session
S: Open settings
Esc: Close modals
```

### Visual Indicators

- High contrast mode option
- Colorblind-friendly palette available
- Larger text option
- Motion reduction mode (disable animations)

---

## Technical Implementation Notes

### Frontend Framework Recommendation

**Electron + React** for desktop application:
- Native system integration
- Cross-platform (Mac/Windows/Linux)
- Access to file system
- System tray integration

### State Management

```javascript
SessionState {
  status: 'idle' | 'recording' | 'paused' | 'reviewing',
  currentSession: {
    id: string,
    name: string,
    startTime: timestamp,
    metadata: {...},
    spectralData: RingBuffer,
    burstEvents: Array,
    quality: {...}
  },
  stream: {
    connected: boolean,
    device: string,
    sampleRate: number,
    channels: Array
  }
}
```

### Real-Time Updates

```javascript
// WebSocket connection to burst recorder
ws.on('burst_detected', (data) => {
  updateBurstCounter(data);
  addBurstEvent(data);
  flashNotification(data);
});

// Polling for spectral metrics (every 1 second)
setInterval(() => {
  fetchSpectralBands().then(updateBandDisplay);
}, 1000);
```

### Data Persistence

```
~/Documents/eeg-sessions/
├── 2025-11-11_meditation_20-15/
│   ├── session.json          # Metadata
│   ├── spectral_data.csv     # Frequency bands
│   ├── bursts/
│   │   ├── burst_0001.npz
│   │   ├── burst_0001_meta.json
│   │   └── ...
│   └── analysis/
│       ├── cleaned_spectral.csv
│       └── summary_report.pdf
```

---

## User Testing Scenarios

### Scenario 1: First-Time User

**Goal**: Record first meditation session

**Steps:**
1. Open app, see "Get Started" tutorial
2. Click "New Session"
3. Name: "My First Meditation"
4. Leave defaults (spectral + burst)
5. Click "Start Recording"
6. Meditate for 10 minutes
7. Click "Stop"
8. Review summary screen
9. Export data

**Success Criteria:**
- ✓ User completes recording without confusion
- ✓ Understands what data was captured
- ✓ Can find exported files

### Scenario 2: Advanced User

**Goal**: Compare two meditation techniques

**Steps:**
1. Record Session A: "Breath Focus" (20 min)
2. Record Session B: "Body Scan" (20 min)
3. Open both in review screen
4. Compare theta peaks
5. Export side-by-side comparison

**Success Criteria:**
- ✓ Easy to locate past sessions
- ✓ Clear visual comparison
- ✓ Can correlate bursts with technique differences

### Scenario 3: Artifact Cleaning

**Goal**: Get clean spectral data from noisy session

**Steps:**
1. Record session with deliberate movements
2. Review burst events
3. Click "Generate Clean CSV"
4. Export artifact-free spectral data

**Success Criteria:**
- ✓ Burst events clearly identified
- ✓ Clean data excludes artifact windows
- ✓ User understands the cleaning process

---

## Future Enhancements

### Phase 2 Features

- [ ] Multi-session comparison dashboard
- [ ] Session templates (meditation, focus, sleep)
- [ ] Cloud sync for cross-device access
- [ ] Shareable session reports
- [ ] Integration with neurofeedback protocols

### Phase 3 Features

- [ ] Machine learning artifact classification
- [ ] Personalized threshold recommendations
- [ ] Session scheduling and reminders
- [ ] Community features (anonymized data sharing)
- [ ] Advanced analytics (coherence, phase-locking)

---

## Implementation Roadmap

### Week 1: Core UI
- Session configuration panel
- Start/stop controls
- Basic recording timer

### Week 2: Real-Time Monitoring
- Spectral band display
- Burst event list
- Quality indicators

### Week 3: Session Review
- Historical session list
- Detailed review screen
- Export functionality

### Week 4: Polish
- Settings panel
- Keyboard shortcuts
- Tutorial/onboarding

---

**Next Step**: Create interactive HTML prototype for user testing?
