# Event-Triggered EEG Burst Recorder

**For Neurable MW75 Neuro Headphones**

Automatically detects and records EEG bursts when signal exceeds configurable thresholds. Integrates with Neurable's LSL streaming and realtime viewer.

## Features

- 🔥 **Event-Triggered Recording** - Automatically captures bursts when RMS or P2P thresholds exceeded
- 📊 **LSL Integration** - Connects to Neurable Research Kit EEG stream
- 🎯 **Event Markers** - Sends burst markers to realtime viewer for synchronized visualization
- 💾 **Smart Data Capture** - Saves pre-burst + post-burst windows (configurable)
- 📁 **NPZ + JSON Output** - Compressed EEG data + human-readable metadata
- ⚡ **Real-time Processing** - Minimal latency, circular buffer architecture

## System Architecture

```
MW75 Neuro Headphones
         ↓
[Neurable Research Kit App]
         ↓ (LSL stream type='EEG')
         ├─→ [Burst Recorder] ← This tool
         │        ↓
         │    Detects bursts
         │        ↓
         │    Sends markers → [Realtime Viewer]
         │        ↓
         │    Saves burst data
         │
         └─→ [Realtime Viewer] ← Shows live visualization
                  ↓
              Displays burst markers as vertical lines
```

## Installation

### 1. Install Python Dependencies

```bash
cd eeg-burst-recorder
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Neurable Research Kit

Install the visualizer for your Mac:
```bash
open ~/Downloads/Neurable\ Research\ Kit\ EEG\ Visualizer-Installer-MacOS-Silicon-arm64.dmg
```

Follow the installer instructions.

### 3. Set Up Realtime Viewer (Optional but Recommended)

```bash
cd ~/Downloads/eeg-realtime-viewer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

### Option 1: Burst Recorder Only

```bash
# Activate environment
source venv/bin/activate

# Run with default settings
python burst_recorder.py

# Or customize thresholds
python burst_recorder.py --threshold-rms 60 --threshold-p2p 120
```

### Option 2: Full Stack (Recorder + Realtime Viewer)

**Terminal 1:** Launch Neurable Research Kit
- Open the app from Applications
- Put on your MW75 Neuro headphones
- Start streaming

**Terminal 2:** Start Realtime Viewer
```bash
cd ~/Downloads/eeg-realtime-viewer
source venv/bin/activate
python run_viewer.py --source lsl
```

**Terminal 3:** Start Burst Recorder
```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate
python burst_recorder.py --threshold-rms 50 --threshold-p2p 100
```

Now:
- Realtime viewer shows live EEG
- Burst recorder monitors for events
- When burst detected, vertical marker appears in viewer
- Burst data saved to `burst_data/` directory

## Usage

```bash
python burst_recorder.py [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--threshold-rms` | float | 50.0 | RMS threshold for burst detection (µV) |
| `--threshold-p2p` | float | 100.0 | Peak-to-peak threshold for burst detection (µV) |
| `--pre-burst` | float | 1.0 | Seconds of data to save before burst |
| `--post-burst` | float | 2.0 | Seconds of data to save after burst |
| `--output-dir` | string | burst_data | Directory to save burst data |
| `--duration` | float | ∞ | Recording duration in seconds (infinite if not set) |
| `--no-markers` | flag | - | Disable sending LSL event markers |
| `--stream-type` | string | EEG | LSL stream type to connect to |

### Examples

**High-sensitivity burst detection:**
```bash
python burst_recorder.py --threshold-rms 30 --threshold-p2p 60
```

**Longer burst windows:**
```bash
python burst_recorder.py --pre-burst 2.0 --post-burst 3.0
```

**60-second test recording:**
```bash
python burst_recorder.py --duration 60
```

**Save to custom directory:**
```bash
python burst_recorder.py --output-dir my_experiment_data
```

## Output Files

Each detected burst creates two files:

### 1. NPZ File (EEG Data)
`burst_20251110_123456_0001.npz`

Contains:
- `data`: EEG samples (numpy array, shape: samples × channels)
- `sample_rate`: Sampling frequency (Hz)
- `channel_names`: List of channel labels
- `timestamp`: ISO format timestamp
- `channels`: List of channels that triggered the burst
- `all_metrics`: RMS/P2P values for all channels

Load with:
```python
import numpy as np
burst = np.load('burst_20251110_123456_0001.npz')
data = burst['data']
sample_rate = burst['sample_rate']
```

### 2. JSON File (Metadata)
`burst_20251110_123456_0001_meta.json`

Human-readable metadata:
```json
{
  "burst_id": "burst_20251110_123456_0001",
  "sample_rate": 256.0,
  "n_samples": 768,
  "n_channels": 8,
  "channel_names": ["CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4"],
  "pre_burst_seconds": 1.0,
  "post_burst_seconds": 2.0,
  "thresholds": {
    "rms": 50.0,
    "p2p": 100.0
  },
  "timestamp": "2025-11-10T12:34:56.789123",
  "channels": [
    {
      "channel": "C3",
      "rms": 62.3,
      "p2p": 145.7
    }
  ]
}
```

## Tuning Thresholds

### Finding the Right Thresholds

1. **Start with defaults** and monitor for a few minutes
2. **Too many bursts?** Increase thresholds
3. **Too few bursts?** Decrease thresholds

### Typical Values

| Activity | RMS (µV) | P2P (µV) | Notes |
|----------|----------|----------|-------|
| Resting/Meditation | 20-30 | 40-60 | Very sensitive |
| Normal activity | 40-60 | 80-120 | Balanced |
| High activity/artifacts | 80-100 | 160-200 | Less sensitive |

### Channel-Specific Patterns

- **Frontal (F5, F6)**: More artifact-prone (eye blinks)
- **Central (C3, C4)**: Motor activity bursts
- **Parietal (PO3, PO4)**: Visual/attention bursts

## Troubleshooting

### "No EEG stream found"

1. Check Neurable Research Kit is running
2. Verify headphones are connected and paired
3. Ensure streaming is started in the app
4. Try increasing timeout: `--stream-timeout 30`

### Too Many False Positives

- Increase thresholds: `--threshold-rms 80 --threshold-p2p 160`
- Check for artifacts (eye blinks, jaw clenches)
- Ensure good electrode contact

### Missing Dependencies

```bash
pip install --upgrade numpy pylsl
```

### Realtime Viewer Not Showing Markers

- Check burst recorder started with markers enabled (default)
- Verify both apps connected to same LSL stream
- Look for "✓ Event marker outlet created" in recorder output

## Integration with Analysis

### Load Burst Data

```python
import numpy as np
import json
from pathlib import Path

# Load burst
burst_file = 'burst_data/burst_20251110_123456_0001.npz'
meta_file = 'burst_data/burst_20251110_123456_0001_meta.json'

# Load EEG data
data = np.load(burst_file)
eeg_samples = data['data']  # Shape: (samples, channels)
sample_rate = float(data['sample_rate'])
channels = data['channel_names'].tolist()

# Load metadata
with open(meta_file) as f:
    meta = json.load(f)

print(f"Burst: {meta['burst_id']}")
print(f"Triggered by: {[ch['channel'] for ch in meta['channels']]}")
print(f"Data shape: {eeg_samples.shape}")
```

### Analyze Burst

```python
import matplotlib.pyplot as plt

# Plot all channels
fig, axes = plt.subplots(len(channels), 1, figsize=(12, 8), sharex=True)
time_axis = np.arange(len(eeg_samples)) / sample_rate

for i, (ax, channel) in enumerate(zip(axes, channels)):
    ax.plot(time_axis, eeg_samples[:, i])
    ax.set_ylabel(f'{channel} (µV)')
    ax.axvline(meta['pre_burst_seconds'], color='r', linestyle='--', label='Burst trigger')

axes[-1].set_xlabel('Time (s)')
plt.tight_layout()
plt.show()
```

## 🧠 MindMeld Pipeline (New!)

**Real-time Audio-LSL Sync + Grok JSON Export + ML State Analysis**

The MindMeld edition adds voice-brain correlation for meditation and conversation analysis with Grok AI integration.

### What's New

- 🎤 **Audio-LSL Sync**: Captures voice/audio aligned to EEG bursts via LSL timestamps
- 📦 **Grok JSON Export**: Compressed `.json.snappy` files with EEG/audio/metrics/insights
- 🤖 **ML State Analysis**: Automatic band power analysis and state classification (relax/alert/neutral)
- 💬 **Continuous Mode**: Record fixed-duration chunks for conversations (not just bursts)
- 🎯 **YAML Config**: Pre-configured settings for meditation vs conversation sessions

### Installation

Install additional MindMeld dependencies:

```bash
pip install pyaudio scipy pandas scikit-learn python-snappy pyyaml
```

### Quick Start

#### Meditation Session (Burst Mode)

```bash
python scripts/run_mindmeld.py --session my_meditation --mode burst
```

#### Conversation Analysis (Continuous Mode)

```bash
python scripts/run_mindmeld.py --session grok_talk --mode continuous --duration 300
```

### Configuration

Edit `config/meditation.yaml` for custom settings:

```yaml
thresholds:
  rms: 25.0  # Lower threshold for calm states
  p2p: 50.0

audio:
  enable: true
  lsl_stream_name: "Audio"
  sample_rate: 44100

tags: ["grok_chat", "meditation"]
```

### Output Format

MindMeld creates enhanced exports in `.json.snappy` format:

```json
{
  "burst_id": "burst_20251111_162638_0001",
  "eeg": {
    "data": [[...], [...]],
    "sample_rate": 500.0,
    "channels": ["Ch1", "Ch2", ...],
    "metrics": {"Ch1": {"rms": 85.2, "p2p": 279.7}, ...}
  },
  "audio": {
    "data": [...],
    "start_ts": 1699726598000,
    "duration": 3.0,
    "lsl_offset_ms": 8.4
  },
  "insights": {
    "dominant_band": "theta",
    "powers": {"delta": 51.26, "theta": 15.24, "alpha": 4.65, "beta": 10.05, "gamma": 14.72},
    "anomaly_score": 0.15,
    "state": "relax"
  },
  "tags": ["meditation", "theta-training"]
}
```

### Analyzing with Grok

1. **Decompress** a `.json.snappy` file:
   ```bash
   python -c "import snappy; print(snappy.uncompress(open('burst_data/session_001/burst_*.json.snappy','rb').read()).decode())"
   ```

2. **Copy** the JSON output

3. **Paste to Grok** with a prompt like:
   - "Analyze this EEG meditation session for theta/alpha patterns"
   - "Compare my brain state during this conversation vs baseline"
   - "What cognitive patterns emerge during these burst events?"

### MindMeld vs Standard Mode

| Feature | Standard Mode | MindMeld Mode |
|---------|--------------|---------------|
| **Trigger** | RMS/P2P thresholds | Threshold OR continuous chunks |
| **Audio** | ❌ Not captured | ✅ LSL-synced audio |
| **Export** | NPZ + JSON | NPZ + JSON + `.json.snappy` (Grok-ready) |
| **Analysis** | Basic metrics | ML band power + state classification |
| **Use Case** | Burst detection | Meditation + conversation analysis |

### Tuning for Meditations

For subtle theta/alpha detection during calm states:

```yaml
thresholds:
  rms: 20.0  # Very sensitive
  p2p: 40.0  # Catches alpha dips
```

**Channels to watch**: Frontal (F5, F6) for artifacts, Parietal (PO3, PO4) for meditation states

### Continuous Mode (Conversations)

For steady streaming during talks with Grok:

```bash
python scripts/run_mindmeld.py --session grok_convo --mode continuous --duration 600
```

- **Chunk size**: 30 seconds (configurable in code)
- **Output**: Fixed-interval snapshots instead of threshold-triggered bursts
- **Best for**: Conversations, lectures, extended focus sessions

### Advanced: Direct CLI Use

Bypass the launcher for full control:

```bash
python burst_recorder.py \
  --config config/meditation.yaml \
  --enable-audio \
  --mode continuous \
  --threshold-rms 25 \
  --duration 120 \
  --output-dir burst_data/custom_session
```

## Advanced Usage

### Custom Event Detection

Extend `EEGBurstRecorder` class to implement custom detection algorithms:

```python
from burst_recorder import EEGBurstRecorder
import numpy as np

class CustomBurstRecorder(EEGBurstRecorder):
    def detect_burst(self, data):
        # Your custom algorithm
        spectral_power = np.abs(np.fft.rfft(data, axis=0))**2
        alpha_band = spectral_power[8:13].sum()  # 8-13 Hz

        if alpha_band > custom_threshold:
            return {
                'timestamp': datetime.now().isoformat(),
                'alpha_power': float(alpha_band),
                'channels': [...]
            }
        return None
```

## License

MIT License - See LICENSE file

## Credits

- Built for **Neurable MW75 Neuro** headphones
- Integrates with **Neurable Research Kit**
- Uses **Lab Streaming Layer (LSL)** protocol
- Compatible with Neurable's **EEG Realtime Viewer**

## Support

For issues with:
- **This tool**: Check GitHub issues
- **Neurable hardware**: Contact Neurable support
- **LSL protocol**: See [LSL documentation](https://labstreaminglayer.readthedocs.io/)
