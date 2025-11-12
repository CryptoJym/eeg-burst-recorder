# Grok Analysis Workflow - Complete Guide

**Date**: January 11, 2025
**Purpose**: How to use MindMeld burst exports with Grok AI for brain activity analysis

---

## 🎯 Overview: Why Grok?

The MindMeld pipeline exports bursts as **snappy-compressed JSON** because:

1. **Compact Storage**: 200KB compressed vs 2MB uncompressed
2. **AI-Friendly Format**: JSON is perfect for LLM analysis
3. **Complete Context**: EEG + audio + ML insights in one file
4. **Grok Integration**: Designed for xAI's Grok to analyze brain-voice correlation

---

## 📦 What's Inside a `.json.snappy` File?

Each burst export contains:

```json
{
  "burst_id": "burst_20251111_180753_0001",
  "timestamp": "2025-01-11T18:07:53.123Z",
  "tags": ["meditation", "grok_chat"],

  "eeg": {
    "data": [[...1500 samples × 8 channels...]],
    "sample_rate": 500.0,
    "channels": ["CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4"],
    "duration": 3.0,
    "metrics": {
      "C3": {"rms": 62.3, "p2p": 145.7, "mean": -2.1},
      "F5": {"rms": 58.9, "p2p": 138.2, "mean": 1.4},
      ...
    }
  },

  "audio": {
    "data": [...132300 samples...],
    "start_ts": 1699726598000,
    "duration": 3.0,
    "sample_rate": 44100,
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
  },

  "config": {
    "thresholds": {"rms": 25.0, "p2p": 50.0},
    "mode": "burst"
  }
}
```

---

## 🔧 Step 1: Extract and Decompress Burst Files

### Option A: Single Burst Analysis

```bash
cd ~/Downloads/eeg-burst-recorder/burst_data/[session_name]

# List all burst exports
ls -lh *.json.snappy

# Decompress a specific burst
python3 << 'EOF'
import snappy
import json

# Read compressed file
with open('burst_20251111_180753_0001.json.snappy', 'rb') as f:
    compressed = f.read()

# Decompress
decompressed = snappy.uncompress(compressed)
data = json.loads(decompressed.decode('utf-8'))

# Pretty print
print(json.dumps(data, indent=2))
EOF
```

**Output**: Pretty JSON ready to paste into Grok

### Option B: Batch Analysis (Multiple Bursts)

```bash
# Extract all bursts from a session
python3 << 'EOF'
import snappy
import json
from pathlib import Path

session_dir = Path('burst_data/meditation_session_001')
bursts = []

for snappy_file in sorted(session_dir.glob('burst_*.json.snappy')):
    with open(snappy_file, 'rb') as f:
        data = json.loads(snappy.uncompress(f.read()).decode('utf-8'))
        bursts.append(data)

# Create summary for Grok
summary = {
    'session': str(session_dir.name),
    'total_bursts': len(bursts),
    'bursts': bursts
}

print(json.dumps(summary, indent=2))
EOF
```

**Output**: Multi-burst session ready for Grok analysis

---

## 💬 Step 2: Grok Analysis Prompts

### Prompt Template 1: Single Burst Analysis

```
I recorded EEG brain activity during meditation using MW75 headphones.
Here's a 3-second burst with synchronized audio. Please analyze:

1. What brain state am I in? (relaxed, alert, focused, etc.)
2. Which brain regions are most active?
3. Is the audio correlated with brain activity patterns?
4. Are there any unusual patterns or anomalies?

[PASTE DECOMPRESSED JSON HERE]
```

**What Grok Will Tell You**:
- Dominant frequency band interpretation (theta = relaxed, alpha = calm, beta = alert)
- Channel activity patterns (frontal = thinking, parietal = sensory)
- Audio-EEG correlation (did speaking trigger certain patterns?)
- Anomaly detection (anything unusual?)

### Prompt Template 2: Meditation Session Analysis

```
I completed a 10-minute meditation session with 12 detected bursts.
Each burst represents a moment of heightened brain activity.

Please analyze this session:
1. Overall meditation quality (based on alpha/theta patterns)
2. Progression over time (am I getting deeper into meditation?)
3. Correlate bursts with audio events (e.g., breath sounds, movements)
4. Identify the "deepest" meditation moments

[PASTE MULTI-BURST JSON HERE]
```

**What Grok Will Tell You**:
- Session quality score
- Timeline of brain state transitions
- Best moments (highest alpha, lowest beta)
- Audio-triggered vs spontaneous bursts

### Prompt Template 3: Conversation Analysis

```
I recorded EEG during a 5-minute conversation using continuous mode.
This captured my brain activity while talking with Grok AI.

Analyze this conversation:
1. When is my brain most active? (speaking vs listening)
2. Do certain topics trigger specific brain patterns?
3. Theta spikes (deep thinking) vs beta spikes (active processing)
4. Gamma bursts (aha moments)

[PASTE CONTINUOUS MODE CHUNKS HERE]
```

**What Grok Will Tell You**:
- Speaking vs listening brain signatures
- Topic-brain pattern correlation
- Cognitive load indicators
- Moments of insight/understanding

---

## 🧪 Step 3: Practical Examples

### Example 1: "Why Did I Get a Burst During Meditation?"

**Your Question to Grok**:
```
At 18:07:53, I got this burst during eyes-closed meditation.
I think I was blinking or shifting position. Can you confirm?

Audio shows [describe what you hear in the audio data]
EEG shows high activity in frontal channels (F5, F6)

What actually triggered this burst?

[PASTE BURST JSON]
```

**Grok's Analysis**:
- "High F5/F6 activity with P2P > 140µV indicates eye movement artifact (blink)"
- "Audio shows faint rustling at 1.2s - likely head movement"
- "Theta increase post-artifact suggests re-settling into meditation"
- "Recommendation: Lower P2P threshold to 75µV to capture subtler states"

### Example 2: "Am I Meditating Correctly?"

**Your Question to Grok**:
```
Session: 10 minutes, 8 bursts detected
Config: RMS 25µV, P2P 50µV
Tags: ["first_meditation", "eyes_closed"]

I'm new to meditation. Based on these bursts:
1. Am I doing it right?
2. Should I adjust thresholds?
3. What patterns indicate "good" meditation?

[PASTE SESSION JSON]
```

**Grok's Analysis**:
- "Strong theta (15-24%) and alpha (8-12%) indicate successful meditation state"
- "Burst frequency decreasing over time = brain settling down (good)"
- "Frontal beta still elevated = active thinking (common for beginners)"
- "Recommendation: Try 5-minute sessions first, gradually increase"

### Example 3: "Conversation Brain Patterns"

**Your Question to Grok**:
```
I recorded my brain while talking to you (Grok) for 2 minutes.
Continuous mode captured 30-second chunks.

When I asked complex questions:
- Chunk 1: "Explain quantum entanglement"
- Chunk 2: "What's for dinner?" (simple)
- Chunk 3: Listening to your answer

Compare brain activity across these chunks.

[PASTE 3 CHUNKS JSON]
```

**Grok's Analysis**:
- "Chunk 1: Beta spike (18Hz) + gamma (35Hz) = active reasoning"
- "Chunk 2: Low beta, stable alpha = automatic/casual thinking"
- "Chunk 3: Theta increase (6Hz) = processing new information"
- "Observation: Your brain clearly differentiates question complexity"

---

## 🚀 Step 4: Advanced Workflows

### Workflow 1: Daily Meditation Tracking

```bash
# Setup cron job to record daily meditation
cat > ~/daily_meditation.sh << 'EOF'
#!/bin/bash
SESSION="meditation_$(date +%Y%m%d)"
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate
python scripts/run_mindmeld.py \
  --session "$SESSION" \
  --config config/meditation.yaml \
  --mode burst \
  --duration 600
EOF

chmod +x ~/daily_meditation.sh

# Run daily at 7am
echo "0 7 * * * ~/daily_meditation.sh" | crontab -
```

**Weekly Analysis**:
```bash
# Extract last 7 days of meditation data
python3 << 'EOF'
import snappy
import json
from pathlib import Path
from datetime import datetime, timedelta

# Get sessions from last 7 days
week_ago = datetime.now() - timedelta(days=7)
sessions = []

for session_dir in Path('burst_data').glob('meditation_*'):
    session_date = datetime.strptime(session_dir.name, 'meditation_%Y%m%d')
    if session_date >= week_ago:
        bursts = []
        for f in session_dir.glob('burst_*.json.snappy'):
            with open(f, 'rb') as fp:
                bursts.append(json.loads(snappy.uncompress(fp.read())))
        sessions.append({
            'date': session_date.isoformat(),
            'bursts': bursts
        })

# Ask Grok: "Analyze my meditation progress over the past week"
print(json.dumps({'weekly_meditation': sessions}, indent=2))
EOF
```

### Workflow 2: Real-Time Grok Feedback (Future Enhancement)

**Concept**: Stream bursts to Grok API in real-time

```python
# Future implementation (requires Grok API access)
import asyncio
import aiohttp

async def analyze_burst_realtime(burst_data):
    """Send burst to Grok API for immediate analysis"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://api.x.ai/v1/analyze',
            headers={'Authorization': 'Bearer YOUR_GROK_API_KEY'},
            json={
                'prompt': 'Analyze this EEG burst in real-time:',
                'data': burst_data
            }
        ) as resp:
            analysis = await resp.json()
            return analysis['insights']

# In burst_recorder.py save_burst():
# insights = await analyze_burst_realtime(grok_payload)
# display_in_ui(insights)
```

---

## 📊 What to Look For in Grok's Analysis

### Brain State Indicators

| Pattern | Meaning | Grok Keyword |
|---------|---------|--------------|
| High theta (4-8Hz) | Deep relaxation, creativity | "theta dominance" |
| High alpha (8-13Hz) | Calm focus, eyes closed | "alpha state" |
| High beta (13-30Hz) | Active thinking, alert | "beta activity" |
| Gamma bursts (30-100Hz) | Insight, "aha!" moments | "gamma spike" |
| Low frequency drift | Drowsiness, falling asleep | "delta increase" |

### Channel Activity

| Channels | Brain Region | Activity Indicates |
|----------|--------------|-------------------|
| F5, F6 | Frontal (forehead) | Thinking, planning, eye movement |
| C3, C4 | Central (motor) | Movement preparation, execution |
| CP3, CP4 | Parietal (sensory) | Sensory processing, spatial awareness |
| PO3, PO4 | Parieto-occipital | Visual processing, alpha rhythm |

### Anomaly Scores

- **0.0-0.1**: Normal brain activity
- **0.1-0.3**: Unusual but not alarming (e.g., strong focus)
- **0.3-0.5**: Significant deviation (investigate)
- **0.5+**: Very unusual (check for artifacts)

---

## 🎯 Putting It All Together: Complete Session Workflow

### 1. Record Session with MindMeld

```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate

# Meditation session (burst mode)
python scripts/run_mindmeld.py \
  --session "morning_meditation" \
  --config config/meditation.yaml \
  --mode burst \
  --duration 600

# OR conversation session (continuous mode)
python scripts/run_mindmeld.py \
  --session "grok_conversation" \
  --mode continuous \
  --duration 300
```

### 2. Extract for Grok

```bash
cd burst_data/morning_meditation

# Quick extract single burst
python3 -c "
import snappy, json
with open('burst_20251111_180753_0001.json.snappy', 'rb') as f:
    print(json.dumps(json.loads(snappy.uncompress(f.read())), indent=2))
" > burst_for_grok.json

# Copy to clipboard (Mac)
cat burst_for_grok.json | pbcopy

# Or save all bursts
python3 -c "
import snappy, json
from pathlib import Path
bursts = []
for f in sorted(Path('.').glob('burst_*.json.snappy')):
    with open(f, 'rb') as fp:
        bursts.append(json.loads(snappy.uncompress(fp.read())))
print(json.dumps({'session': 'morning_meditation', 'bursts': bursts}, indent=2))
" > full_session_for_grok.json
```

### 3. Paste to Grok

Go to **https://grok.x.ai** or **https://twitter.com** (Grok tab)

**Your Prompt**:
```
I just completed a 10-minute meditation session with EEG brain monitoring.
I recorded 8 bursts of heightened brain activity.

Each burst includes:
- 8-channel EEG data (500Hz, 3 seconds)
- Synchronized audio from microphone
- ML-computed band powers and state classification

Please analyze this session:
1. Overall meditation quality
2. Brain state progression over time
3. Best moments (deepest relaxation)
4. Recommendations for improving my practice

Here's the data:

[PASTE CONTENTS OF full_session_for_grok.json]
```

### 4. Interpret Grok's Response

Grok will provide:
- **Session Quality Score**: "7/10 - Good meditation with room for improvement"
- **State Analysis**: "Started alert (beta), transitioned to relaxed (theta) at 3:24"
- **Peak Moments**: "Burst #4 (4:32) shows deepest alpha - replicate this!"
- **Recommendations**: "Lower RMS threshold to 20µV to capture subtler states"

### 5. Iterate and Improve

Based on Grok's feedback:
```bash
# Update config with new thresholds
cat > config/meditation_refined.yaml << 'EOF'
thresholds:
  rms: 20.0  # Lowered based on Grok recommendation
  p2p: 40.0  # More sensitive to subtle states

audio:
  enable: true
  sample_rate: 44100

tags: ["meditation", "grok_optimized"]
EOF

# Try again
python scripts/run_mindmeld.py \
  --session "morning_meditation_v2" \
  --config config/meditation_refined.yaml \
  --mode burst \
  --duration 600
```

---

## 🔮 Future Enhancements

### 1. Grok API Integration (When Available)

```python
# Real-time analysis during recording
class GrokRealtimeAnalyzer:
    async def analyze_burst(self, burst_data):
        response = await grok_api.analyze(burst_data)
        return response.insights

    async def stream_feedback(self, session):
        async for burst in session:
            insights = await self.analyze_burst(burst)
            ui.display(f"Grok: {insights['state']} - {insights['tips']}")
```

### 2. Voice Annotations

```bash
# Record voice notes during meditation
python scripts/run_mindmeld.py \
  --session "meditation_with_notes" \
  --enable-voice-annotations \
  --mode burst
```

### 3. Multi-Session Comparison

```bash
# Compare today vs yesterday
python tools/compare_sessions.py \
  meditation_20251110 \
  meditation_20251111 \
  --output grok_comparison.json
```

---

## ✅ Quick Reference Card

### Decompress Single Burst
```bash
python3 -c "import snappy,json; print(json.dumps(json.loads(snappy.uncompress(open('burst.json.snappy','rb').read())),indent=2))"
```

### Extract All Bursts
```bash
python3 -c "import snappy,json; from pathlib import Path; print(json.dumps([json.loads(snappy.uncompress(open(f,'rb').read())) for f in sorted(Path('.').glob('burst_*.json.snappy'))],indent=2))"
```

### Copy to Clipboard (Mac)
```bash
python3 -c "..." | pbcopy
```

### Best Grok Prompt
```
"Analyze this EEG burst from meditation. What brain state am I in and how can I improve?"
[PASTE JSON]
```

---

**The MindMeld → Grok pipeline is your personal brain activity analyzer!** 🧠🤖
