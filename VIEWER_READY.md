# 🎉 MindMeld Session Viewer is LIVE!

## 🌐 Open in Your Browser

**Click this link or copy it to your browser:**

```
http://localhost:5001
```

---

## 📊 What You'll See

### **Main Dashboard**
- **Top Stats Bar**: Total sessions, bursts, and brain state counts
- **Left Sidebar**: All your recording sessions (sorted newest first)
- **Main Area**: Burst cards and detailed analysis

### **Your Current Session**
You have **1 session** with **4 bursts** captured:
- Session: `quick_test_20251111_180728`
- Each burst has full EEG data + audio + ML insights

---

## 🎯 How to Use the Viewer

### **Step 1: Click on a Session** (left sidebar)
- Click on `quick_test_20251111_180728`
- You'll see 4 purple gradient cards, one for each burst

### **Step 2: Click on a Burst Card**
- Each card shows:
  - 🧠 **Brain state**: relax, alert, or neutral
  - 🎵 **Dominant frequency band**: delta, theta, alpha, beta, or gamma
  - ⏱️ **Timestamp**: when the burst occurred

### **Step 3: Explore Burst Details**
When you click a burst, you'll see:

1. **📊 Brain State Insights**
   - State: relax/alert/neutral
   - Dominant Band: which frequency was strongest
   - Anomaly Score: 0.0-1.0 (higher = more unusual)
   - Sample Rate: 500 Hz

2. **🎵 Frequency Band Powers** (interactive bars)
   - Delta (0.5-4 Hz): Deep sleep, unconscious
   - Theta (4-8 Hz): Meditation, creativity
   - Alpha (8-13 Hz): Relaxed awareness
   - Beta (13-30 Hz): Active thinking, focus
   - Gamma (30-100 Hz): Peak concentration

3. **📈 EEG Waveform** (interactive plot)
   - All 8 channels visualized
   - Zoom, pan, hover for values
   - See the actual brain activity!

4. **🤖 Grok Export** (JSON data)
   - Click "📋 Copy to Clipboard" button
   - Paste directly to Grok for AI analysis
   - Includes EEG + audio + insights

---

## 🔍 Understanding Your Data

### **Brain States**
- **relax** 🧘 - Theta/alpha dominant (meditation, calm)
- **alert** ⚡ - Beta/gamma dominant (focus, active thinking)
- **neutral** 😐 - Delta or mixed (baseline state)

### **Frequency Bands**
Each band tells you something about your mental state:

| Band | Frequency | Mental State |
|------|-----------|--------------|
| **Delta** | 0.5-4 Hz | Deep sleep, unconscious processing |
| **Theta** | 4-8 Hz | Meditation, light sleep, creativity |
| **Alpha** | 8-13 Hz | Relaxed awareness, eyes closed |
| **Beta** | 13-30 Hz | Active thinking, focus, problem-solving |
| **Gamma** | 30-100 Hz | Peak concentration, insight |

### **Anomaly Score**
- **0.0-0.2**: Normal brain activity
- **0.2-0.5**: Slightly unusual (could be interesting insight!)
- **0.5+**: High engagement, stress, or artifact

---

## 💡 Tips for Analysis

### **Compare Bursts**
- Look at multiple bursts in a session
- Notice patterns: Are you mostly "relax" or "alert"?
- Check which band is dominant across bursts

### **Use Grok for Deep Insights**
1. Click a burst
2. Scroll to "🤖 Grok Export"
3. Click "📋 Copy to Clipboard"
4. Open Grok (or any AI chat)
5. Paste the JSON
6. Ask questions like:
   - "Analyze this EEG session for meditation patterns"
   - "What cognitive state was I in during this burst?"
   - "Compare my theta and alpha power - what does this mean?"

### **Interactive Waveform**
- **Hover** over lines to see exact values
- **Click and drag** to zoom in on interesting sections
- **Double-click** to reset zoom
- **Click legend items** to hide/show channels

---

## 🔧 Viewer Controls

### **Start the Viewer** (if you closed it)
```bash
cd ~/Downloads/eeg-burst-recorder
./launch_mindmeld_viewer.sh
```

### **Stop the Viewer**
Press `Ctrl+C` in the terminal where it's running

Or find and kill the process:
```bash
pkill -f mindmeld_viewer
```

### **View Logs**
```bash
tail -f ~/Downloads/eeg-burst-recorder/mindmeld_viewer.log
```

---

## 📁 Your Data Location

All your bursts are stored in:
```
~/Downloads/eeg-burst-recorder/burst_data/quick_test_20251111_180728/
```

Files for each burst:
- `burst_*.npz` - EEG samples (NumPy format)
- `burst_*_meta.json` - Human-readable metadata
- `burst_*.json.snappy` - Compressed Grok export

---

## 🎨 UI Features

- **Purple gradient theme** - Easy on the eyes
- **Responsive design** - Works on any screen size
- **Real-time stats** - Updates as you explore
- **One-click copy** - Easy Grok integration
- **Interactive plots** - Zoom, pan, explore your brain data!

---

## 🚀 Next Steps

1. **Open the viewer**: http://localhost:5001
2. **Click your session** in the left sidebar
3. **Explore your 4 bursts** - see which state you were in!
4. **Copy a Grok export** and ask AI to analyze it
5. **Record more sessions** with different activities:
   - Meditation (eyes closed, calm)
   - Active thinking (solving problems)
   - Conversation (talking out loud)

---

## 🎯 Quick Reference

| Action | How To |
|--------|--------|
| **View sessions** | Click sidebar items |
| **See burst details** | Click purple burst cards |
| **Zoom waveform** | Click and drag on plot |
| **Copy for Grok** | Click "📋 Copy to Clipboard" |
| **Start new session** | Use `./start_session.sh` |
| **Open viewer** | http://localhost:5001 |

---

**Enjoy exploring your brain data! 🧠✨**
