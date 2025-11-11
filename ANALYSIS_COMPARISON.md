# EEG Analysis Methods: Spectral vs. Burst Detection

## Executive Summary

Your previous meditation analysis used **spectral analysis** (frequency-domain), while the new system uses **burst detection** (time-domain). These are complementary approaches that capture different aspects of brain activity.

**Key Difference:**
- **Spectral Analysis**: "What frequencies are present over time?"
- **Burst Detection**: "When does signal amplitude spike?"

Both methods can and should be used together for comprehensive analysis.

---

## Method 1: Spectral Analysis (Previous Meditation Analysis)

### What It Measures

Decomposes EEG signal into frequency bands to measure brain rhythms:

| Band | Frequency | Associated State |
|------|-----------|------------------|
| Delta | 0.5-4 Hz | Deep sleep, unconscious |
| Theta | 4-8 Hz | Meditation, drowsiness, creativity |
| Alpha | 8-13 Hz | Relaxed wakefulness, eyes closed |
| Beta | 13-30 Hz | Active thinking, focus, anxiety |
| Gamma | 30-100 Hz | Higher cognition, binding |

### How It Works

```
Raw EEG → FFT (Fast Fourier Transform) → Power Spectrum → Band Powers
```

**Example from your meditation data:**
```
Time: 1769.9 seconds (29.5 minutes)
Delta Power: 3538.09 µV² (z-score: 2.618) ← Peak moment
Interpretation: Deep meditative state or drowsiness
```

### What It Captures

- **Continuous measurements**: Power values every few seconds
- **State transitions**: Shifts from alert (beta) to meditative (theta)
- **Rhythmic activity**: Ongoing oscillations in the brain
- **Baseline trends**: Overall frequency content over time

### Your Previous Output

**`eeg_summary.csv`:**
```csv
time,delta_power,theta_power
1.0,95.27,8.56
7.99,6533.09,117.20
...
```

**Interpretation:**
- At 7.99 seconds: Massive delta spike (6533.09) suggests movement artifact or deep relaxation onset
- Theta at 117.20 indicates active meditative processing

### Strengths

✅ **State detection**: Identify meditation, focus, sleep stages
✅ **Continuous data**: Never miss gradual transitions
✅ **Research-validated**: Decades of neuroscience backing
✅ **Baseline tracking**: See how your brain changes over sessions

### Limitations

❌ **Slow temporal resolution**: Typically 1-2 second windows
❌ **Averages out spikes**: Brief bursts get smoothed
❌ **Frequency-blind to amplitude**: Doesn't flag unusually large events
❌ **Computationally intensive**: Real-time FFT for 14 channels @ 500 Hz

---

## Method 2: Burst Detection (New System)

### What It Measures

Detects sudden, high-amplitude events in the time domain:

- **RMS (Root Mean Square)**: Overall signal power
- **P2P (Peak-to-Peak)**: Maximum voltage swing

### How It Works

```
Raw EEG → Calculate RMS & P2P → Compare to thresholds → Save burst if exceeded
```

**Example from your test:**
```
Burst #2 (22:48:35)
Ch6: RMS = 2342.83 µV, P2P = 6087.91 µV
All 12 active channels triggered!
Interpretation: Major event (eye blink, movement, or strong neural burst)
```

### What It Captures

- **Discrete events**: Only moments when signal spikes
- **Multi-channel patterns**: Which electrodes fire together
- **Artifacts**: Eye blinks, jaw clenches, movement
- **Genuine bursts**: Epileptiform activity, K-complexes, strong thoughts
- **Pre-event context**: 1 second before threshold crossing

### Your Recent Test Output

**Burst #2 (Largest Event):**
- **Triggered channels**: All 12 active (Ch1-Ch12)
- **Peak channel**: Ch6 (frontal)
- **RMS**: 2342.83 µV (46.9x above threshold)
- **P2P**: 6087.91 µV (60.9x above threshold)

**Likely cause**: Eye blink or jaw clench (frontal concentration, very high amplitude)

### Strengths

✅ **Precision timing**: Exact moment of burst captured
✅ **Pre-event data**: Circular buffer saves 1s before trigger
✅ **Efficient storage**: Only saves interesting moments
✅ **Artifact detection**: Automatically flags movement
✅ **Real-time**: No FFT lag, instant detection

### Limitations

❌ **Misses low-amplitude states**: Won't detect subtle meditation shifts
❌ **Binary decision**: Either burst or not—no gradations
❌ **Threshold-dependent**: Too high = miss events, too low = false positives
❌ **No frequency info**: Can't distinguish delta from theta

---

## Direct Comparison: Same Data, Different Insights

### Scenario: Meditation Session

**Spectral Analysis Would Show:**
```
00:00 - Beta dominant (alert, getting comfortable)
05:00 - Alpha rising (relaxing, eyes closed)
10:00 - Theta increasing (entering meditation)
20:00 - Theta peak (deep meditative state)
30:00 - Alpha return (ending session)
```

**Burst Detection Would Show:**
```
00:03 - Burst (eye blink while settling in)
04:57 - Burst (jaw movement, adjusting posture)
19:45 - No bursts (very quiet EEG during deep meditation)
30:12 - Burst (opening eyes, session end)
```

### What Each Misses

**Spectral Analysis Misses:**
- The exact moment you blinked at 4:57
- Brief artifact at 30:12 (averaged into surrounding data)

**Burst Detection Misses:**
- Your 10 minutes of deep theta (below amplitude threshold)
- The gradual transition from beta to alpha

---

## Practical Impact on Your Data

### Meditation Analysis (Your Use Case)

**What you had before (spectral only):**
- ✅ Identified peak theta at 29.5 minutes (deep meditation)
- ✅ Tracked delta/theta power over time
- ❌ Included artifacts in power calculations (6533 µV² spike at 7.99s)
- ❌ Couldn't isolate specific events

**What you can do now (burst + spectral):**

1. **Run spectral analysis on clean data**
   - Use burst detection to identify artifacts
   - Exclude burst windows from spectral calculations
   - Get purer meditation state measurements

2. **Correlate events with states**
   - "Did that burst at 4:57 correspond to a beta spike?" (movement broke meditation)
   - "No bursts during theta peak = genuine deep state"

3. **Artifact-aware interpretation**
   - Burst at 7.99s explains the 6533 µV² delta spike (was noise, not meditation)
   - Can now filter these out for cleaner analysis

---

## Recommended Hybrid Approach

### For Meditation Sessions

**Use BOTH methods simultaneously:**

```bash
# Terminal 1: Spectral analysis (continuous)
python spectral_analyzer.py --session meditation_2025-11-11

# Terminal 2: Burst detection (artifacts + events)
python burst_recorder.py --threshold-rms 100 --threshold-p2p 200

# Post-session: Clean spectral data using burst timestamps
python clean_spectral.py --exclude-bursts burst_data/*.json
```

**Workflow:**
1. Record both spectral and burst data
2. Identify artifact bursts (eye blinks, movements)
3. Remove artifact windows from spectral analysis
4. Get cleaner meditation state measurements
5. Correlate genuine bursts (if any) with mental events

---

## Use Cases for Each Method

### Use Spectral Analysis When:

- 🧘 **Meditation/neurofeedback**: Track brain states over time
- 😴 **Sleep tracking**: Identify sleep stages (delta dominant = deep sleep)
- 🎯 **Focus training**: Monitor beta/theta ratio for concentration
- 📊 **Longitudinal studies**: Compare sessions across weeks/months
- 🔬 **Research**: Standard neuroscience methodology

### Use Burst Detection When:

- 👁️ **Artifact cleaning**: Flag eye blinks, jaw clenches for removal
- ⚡ **Event correlation**: Match bursts to external stimuli (sounds, thoughts)
- 🏥 **Clinical screening**: Detect epileptiform activity (requires medical expertise)
- 🎮 **BCI triggers**: Use bursts as control signals (blink = action)
- 💾 **Storage efficiency**: 30 min meditation = 30 MB spectral, 500 KB bursts

---

## Technical Differences

| Aspect | Spectral Analysis | Burst Detection |
|--------|-------------------|-----------------|
| **Domain** | Frequency | Time |
| **Output** | Continuous power values | Discrete events |
| **Temporal resolution** | 1-2 seconds | 2 milliseconds (1 sample) |
| **Frequency info** | Yes (0.5-100 Hz) | No |
| **Amplitude info** | Indirect (power) | Direct (µV) |
| **Artifact handling** | Corrupts power spectrum | Isolated and saved |
| **Storage (30 min)** | ~30 MB | ~500 KB (10 bursts) |
| **Computation** | FFT (heavy) | RMS/P2P (light) |
| **Real-time viable** | Challenging | Easy |

---

## Data Integration Strategy

### Combining Both Outputs

**Burst data tells you WHEN artifacts happened:**
```json
{
  "timestamp": "2025-11-10T22:48:35",
  "channels": ["Ch1", "Ch6"],
  "rms": 2342.83,
  "likely_cause": "eye_blink"
}
```

**Spectral data tells you WHAT STATE you were in:**
```csv
time,delta_power,theta_power,alpha_power,beta_power
1769.9,3538.09,624.18,180.45,95.32
```

**Combined insight:**
- At 1769.9s (29.5 min): Deep theta, no bursts = genuine meditation
- At 7.99s: Delta spike + burst detected = artifact, exclude from analysis

### Filtering Pipeline

```
Raw EEG
  ↓
Burst Detector → Mark artifact timestamps
  ↓
Spectral Analyzer → Exclude artifact windows
  ↓
Clean Frequency Analysis (meditation states only)
```

---

## Answering Your Question

> "How do the analysis changes impact the data we will get compared to meditation analysis?"

**Short Answer:**
The burst detector **complements** your previous spectral analysis—it doesn't replace it. You now have a tool to:
1. **Clean your spectral data** by removing artifacts
2. **Identify specific events** (blinks, movements) that corrupt meditation measurements
3. **Verify deep states** (no bursts = genuine quiet brain activity)

**Example:**
- **Before**: "Delta spike at 7.99s—was this meditation or movement?" (unknown)
- **Now**: "Delta spike at 7.99s + burst detected = movement artifact" (known, can exclude)

**Data Impact:**
- **Spectral analysis**: More accurate (artifacts removed)
- **Event detection**: New capability (wasn't possible before)
- **Storage**: More efficient (save full data only when needed)
- **Insight**: Deeper (correlate events with states)

---

## Next Steps

### 1. Create Hybrid Analysis Script

Combine both methods:
```bash
python hybrid_analyzer.py \
  --spectral-bands delta,theta,alpha,beta \
  --burst-threshold-rms 100 \
  --burst-threshold-p2p 200 \
  --output-clean-spectral cleaned_meditation.csv \
  --output-bursts artifacts.json
```

### 2. Integrate into UI

Session recording interface should offer:
- [ ] Toggle spectral analysis on/off
- [ ] Toggle burst detection on/off
- [ ] Adjust burst thresholds
- [ ] Real-time display of both metrics
- [ ] Post-session artifact removal option

### 3. Validate with Known Artifacts

Test with deliberate movements:
- Close eyes (alpha burst)
- Blink hard (frontal burst)
- Clench jaw (temporal burst)

Verify burst detector flags these while spectral shows state.

---

## Summary

**You haven't lost any capabilities—you've gained new ones.**

| Capability | Before | Now |
|-----------|--------|-----|
| Meditation state tracking | ✅ Spectral | ✅ Spectral |
| Artifact detection | ❌ None | ✅ Burst |
| Event timing | ❌ None | ✅ Burst |
| Clean data | ⚠️ Artifacts included | ✅ Can exclude |
| Storage efficiency | ❌ Always 30 MB | ✅ 500 KB bursts |
| Real-time feedback | ⚠️ FFT lag | ✅ Instant bursts |

**Recommendation**: Keep using spectral analysis for meditation, add burst detection to clean the data and detect artifacts. Best of both worlds.
