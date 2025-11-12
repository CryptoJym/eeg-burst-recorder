"""
EEG State Analyzer with ML

Quick analysis of EEG data for band power extraction and state classification.
Uses PSD for frequency bands and IsolationForest for anomaly detection.
"""

import numpy as np
from scipy.signal import welch
from sklearn.ensemble import IsolationForest


def quick_analyze(eeg_data, fs=500, n_channels=14):
    """
    Analyze EEG data for dominant bands and state classification.

    Args:
        eeg_data: numpy array, shape (n_samples, n_channels) or (n_samples,)
        fs: sample rate in Hz
        n_channels: number of EEG channels

    Returns:
        dict with keys: dominant_band, powers, anomaly_score, state
    """
    # Handle 1D or 2D input
    if eeg_data.ndim == 1:
        eeg_avg = eeg_data
    else:
        eeg_avg = eeg_data.mean(axis=1)  # Average over channels

    # Compute PSD using Welch's method
    f, psd = welch(eeg_avg, fs=fs, nperseg=min(256, len(eeg_avg)))

    # Define frequency bands
    bands = {
        'delta': (0.5, 4),
        'theta': (4, 8),
        'alpha': (8, 13),
        'beta': (13, 30),
        'gamma': (30, 100)
    }

    # Calculate band powers
    powers = {}
    for band, (lo, hi) in bands.items():
        mask = (f >= lo) & (f <= hi)
        if np.any(mask):
            powers[band] = float(np.trapz(psd[mask], f[mask]))
        else:
            powers[band] = 0.0

    # Determine dominant band
    dominant = max(powers, key=powers.get) if powers else 'unknown'

    # ML anomaly detection: IsolationForest for outlier bursts
    anomaly_score = 0.0
    if eeg_data.ndim == 2 and eeg_data.shape[1] >= 2:
        try:
            # Normalize data
            scaler = lambda x: (x - x.mean()) / (x.std() + 1e-10)
            normalized = scaler(eeg_data.T)  # Channels as samples

            # Fit IsolationForest
            iso = IsolationForest(contamination=0.1, random_state=42)
            predictions = iso.fit_predict(normalized)

            # Calculate anomaly score (% of outliers)
            anomaly_score = float(np.mean([1 if pred == -1 else 0 for pred in predictions]))
        except Exception as e:
            print(f"Anomaly detection failed: {e}")
            anomaly_score = 0.0

    # Classify state based on dominant band
    if dominant in ['theta', 'alpha']:
        state = 'relax'
    elif dominant in ['beta', 'gamma']:
        state = 'alert'
    else:
        state = 'neutral'

    return {
        'dominant_band': dominant,
        'powers': powers,
        'anomaly_score': anomaly_score,  # >0.2 suggests high engagement/stress
        'state': state
    }


def analyze_session(burst_list):
    """
    Analyze multiple bursts to find trends.

    Args:
        burst_list: list of dicts with 'eeg_data' and 'sample_rate'

    Returns:
        dict with session-level insights
    """
    if not burst_list:
        return {'error': 'No bursts to analyze'}

    # Aggregate band powers
    all_powers = {band: [] for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']}
    states = []

    for burst in burst_list:
        analysis = quick_analyze(burst['eeg_data'], burst.get('sample_rate', 500))
        for band, power in analysis['powers'].items():
            all_powers[band].append(power)
        states.append(analysis['state'])

    # Calculate averages
    avg_powers = {band: np.mean(powers) if powers else 0
                  for band, powers in all_powers.items()}

    # Most common state
    dominant_state = max(set(states), key=states.count) if states else 'unknown'

    return {
        'num_bursts': len(burst_list),
        'avg_powers': avg_powers,
        'dominant_state': dominant_state,
        'state_distribution': {state: states.count(state) for state in set(states)}
    }
