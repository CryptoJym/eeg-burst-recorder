# MindMeld Pipeline - System Status

**Date**: January 11, 2025
**Branch**: real-time-sync
**Status**: ✅ Ready for Testing

---

## ✅ Installation Complete

All MindMeld dependencies successfully installed:

- ✅ PyAudio 0.2.14 (audio capture)
- ✅ Scipy 1.16.3 (signal processing)
- ✅ Pandas 2.3.3 (data handling)
- ✅ Scikit-learn 1.7.2 (ML analysis)
- ✅ Python-snappy 0.7.3 (compression)
- ✅ PyYAML 6.0.3 (config loading)

## ✅ Module Verification

All imports working:
- ✅ `burst_recorder.py` imports without errors
- ✅ `src.audio_sync.AudioLSLSync` loads correctly
- ✅ `src.analyzer.quick_analyze` available
- ✅ `src.grok_exporter.GrokExport` ready
- ✅ `scripts/run_mindmeld.py` launcher functional
- ✅ `config/meditation.yaml` parsed successfully

## 🎯 Test Checklist

### Prerequisites
1. **Neurable Research Kit** must be running and streaming EEG data
2. **MW75 Neuro headphones** connected and streaming
3. **LSL stream** active (type='EEG')

### Test 1: Burst Mode (Meditation)
```bash
cd ~/Downloads/eeg-burst-recorder
source venv/bin/activate
python scripts/run_mindmeld.py --session test_meditation --mode burst --duration 60
```

**Expected behavior**:
- Connects to LSL EEG stream
- Monitors for bursts exceeding RMS=25µV or P2P=50µV
- Captures audio when burst detected
- Saves 3 files per burst:
  - `burst_data/test_meditation/burst_*.npz` (EEG data)
  - `burst_data/test_meditation/burst_*_meta.json` (metadata)
  - `burst_data/test_meditation/burst_*.json.snappy` (Grok export)
- Displays ML insights (dominant_band, state, anomaly_score)

### Test 2: Continuous Mode (Conversation)
```bash
python scripts/run_mindmeld.py --session test_convo --mode continuous --duration 120
```

**Expected behavior**:
- Records 30-second chunks regardless of burst detection
- Saves chunks every 30 seconds with audio
- Ideal for conversation analysis

### Test 3: Audio Disabled
```bash
python scripts/run_mindmeld.py --session test_no_audio --mode burst --no-audio
```

**Expected behavior**:
- Bursts detected normally
- No audio capture
- `.json.snappy` files have `audio: null`

## 🔍 Verify Output

After running a test session, check:

1. **Session directory created**:
   ```bash
   ls burst_data/test_meditation/
   ```

2. **Decompress Grok export**:
   ```bash
   python -c "import snappy; print(snappy.uncompress(open('burst_data/test_meditation/burst_*.json.snappy','rb').read()).decode())" | head -50
   ```

3. **Check insights**:
   - Look for `dominant_band` (delta/theta/alpha/beta/gamma)
   - Check `state` (relax/alert/neutral)
   - Verify `anomaly_score` is between 0.0-1.0

4. **Verify audio sync**:
   - Check `audio.lsl_offset_ms` is small (<50ms)
   - Verify `audio.duration` matches pre_burst + post_burst

## 🐛 Known Limitations

- **Audio requires LSL stream**: If no LSL Audio stream exists, AudioLSLSync will create one but may not capture data
- **PyAudio hardware**: Requires default audio input device to be configured
- **LSL timing**: Audio sync depends on LSL clock synchronization

## 📊 Next Steps

1. ✅ Dependencies installed
2. ✅ Modules verified
3. ⏳ **Run Test 1** (burst mode with audio)
4. ⏳ **Run Test 2** (continuous mode)
5. ⏳ **Verify Grok export** format
6. ⏳ **Test with Grok** (paste decompressed JSON)

## 🔗 Resources

- **GitHub Branch**: https://github.com/CryptoJym/eeg-burst-recorder/tree/real-time-sync
- **README**: See "🧠 MindMeld Pipeline" section for full documentation
- **Issues**: Report bugs at https://github.com/CryptoJym/eeg-burst-recorder/issues

---

**System is ready for live testing with EEG hardware!**
