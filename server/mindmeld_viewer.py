#!/usr/bin/env python3
"""
MindMeld Session Viewer - Web UI for exploring EEG burst data with ML insights
"""

from flask import Flask, render_template, jsonify, send_file
import json
import numpy as np
from pathlib import Path
import snappy
from datetime import datetime

app = Flask(__name__)

# Base directory for burst data
BURST_DATA_DIR = Path(__file__).parent.parent / 'burst_data'


@app.route('/')
def index():
    """Main viewer page"""
    return render_template('mindmeld_viewer.html')


@app.route('/api/sessions')
def list_sessions():
    """List all available sessions"""
    sessions = []

    if not BURST_DATA_DIR.exists():
        return jsonify({'sessions': []})

    for session_dir in sorted(BURST_DATA_DIR.iterdir(), reverse=True):
        if session_dir.is_dir():
            # Count bursts in this session
            burst_files = list(session_dir.glob('burst_*_meta.json'))

            if burst_files:
                # Get session info from first burst
                with open(burst_files[0]) as f:
                    meta = json.load(f)

                sessions.append({
                    'name': session_dir.name,
                    'num_bursts': len(burst_files),
                    'timestamp': meta.get('timestamp', 'Unknown'),
                    'path': str(session_dir.relative_to(BURST_DATA_DIR))
                })

    return jsonify({'sessions': sessions})


@app.route('/api/session/<path:session_name>')
def get_session(session_name):
    """Get all bursts in a session"""
    session_dir = BURST_DATA_DIR / session_name

    if not session_dir.exists():
        return jsonify({'error': 'Session not found'}), 404

    bursts = []

    for meta_file in sorted(session_dir.glob('burst_*_meta.json')):
        with open(meta_file) as f:
            meta = json.load(f)

        burst_id = meta['burst_id']

        # Check for Grok export
        grok_file = session_dir / f"{burst_id}.json.snappy"
        has_grok = grok_file.exists()

        # Load ML insights if Grok file exists
        insights = None
        audio_info = None
        if has_grok:
            try:
                with open(grok_file, 'rb') as f:
                    grok_data = json.loads(snappy.uncompress(f.read()).decode('utf-8'))
                insights = grok_data.get('insights', {})
                audio_info = grok_data.get('audio', {})
                if audio_info and 'data' in audio_info:
                    audio_info['has_data'] = True
                    audio_info.pop('data', None)  # Don't send full audio data in list
            except Exception as e:
                print(f"Warning: Could not load Grok data for {burst_id}: {e}")

        bursts.append({
            'burst_id': burst_id,
            'timestamp': meta['timestamp'],
            'sample_rate': meta['sample_rate'],
            'n_samples': meta['n_samples'],
            'n_channels': meta['n_channels'],
            'channels': meta['channels'],
            'thresholds': meta.get('thresholds', {}),
            'has_grok': has_grok,
            'insights': insights,
            'audio_info': audio_info
        })

    return jsonify({
        'session': session_name,
        'bursts': bursts
    })


@app.route('/api/burst/<path:session_name>/<burst_id>')
def get_burst_waveform(session_name, burst_id):
    """Get full EEG waveform data for a burst"""
    session_dir = BURST_DATA_DIR / session_name
    npz_file = session_dir / f"{burst_id}.npz"

    if not npz_file.exists():
        return jsonify({'error': 'Burst file not found'}), 404

    # Load NPZ data
    data = np.load(npz_file)
    eeg_data = data['data']
    sample_rate = float(data['sample_rate'])
    channel_names = data['channel_names'].tolist()

    # Convert to list for JSON
    # Downsample if too many points for browser
    max_points = 2000
    if len(eeg_data) > max_points:
        step = len(eeg_data) // max_points
        eeg_data = eeg_data[::step]

    return jsonify({
        'burst_id': burst_id,
        'data': eeg_data.tolist(),
        'sample_rate': sample_rate,
        'channel_names': channel_names,
        'time_axis': (np.arange(len(eeg_data)) / sample_rate).tolist()
    })


@app.route('/api/grok/<path:session_name>/<burst_id>')
def get_grok_export(session_name, burst_id):
    """Get full Grok export (decompressed) for a burst"""
    session_dir = BURST_DATA_DIR / session_name
    grok_file = session_dir / f"{burst_id}.json.snappy"

    if not grok_file.exists():
        return jsonify({'error': 'Grok export not found'}), 404

    try:
        with open(grok_file, 'rb') as f:
            grok_data = json.loads(snappy.uncompress(f.read()).decode('utf-8'))

        # Remove large data arrays for display
        if 'eeg' in grok_data and 'data' in grok_data['eeg']:
            grok_data['eeg']['data'] = f"<{len(grok_data['eeg']['data'])} samples>"

        if 'audio' in grok_data and 'data' in grok_data['audio']:
            audio_len = len(grok_data['audio']['data'])
            grok_data['audio']['data'] = f"<{audio_len} samples>"

        return jsonify(grok_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """Get overall statistics across all sessions"""
    if not BURST_DATA_DIR.exists():
        return jsonify({'error': 'No data directory'})

    total_sessions = 0
    total_bursts = 0
    states = {'relax': 0, 'alert': 0, 'neutral': 0}
    dominant_bands = {}

    for session_dir in BURST_DATA_DIR.iterdir():
        if session_dir.is_dir():
            total_sessions += 1

            for grok_file in session_dir.glob('burst_*.json.snappy'):
                total_bursts += 1
                try:
                    with open(grok_file, 'rb') as f:
                        grok_data = json.loads(snappy.uncompress(f.read()).decode('utf-8'))

                    insights = grok_data.get('insights', {})
                    state = insights.get('state', 'unknown')
                    band = insights.get('dominant_band', 'unknown')

                    if state in states:
                        states[state] += 1

                    dominant_bands[band] = dominant_bands.get(band, 0) + 1
                except:
                    pass

    return jsonify({
        'total_sessions': total_sessions,
        'total_bursts': total_bursts,
        'states': states,
        'dominant_bands': dominant_bands
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧠 MindMeld Session Viewer")
    print("="*60)
    print("\nOpen in browser: http://localhost:5001")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
