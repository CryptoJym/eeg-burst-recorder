"""
EEG State Analyzer with ML and Symbiosis Tokenization

Quick analysis of EEG data for band power extraction and state classification.
Uses PSD for frequency bands and IsolationForest for anomaly detection.

Symbiosis v1.2: Consciousness token computation with:
- Token_t = H[S_t · PE_t · Φ_t · GA_t] (master equation)
- SE-gated hierarchical prediction error
- Integrated information proxy (Φ)
- Global availability via gamma synchrony (GA)
"""

import numpy as np
from scipy.signal import welch
from scipy.linalg import det
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


# ===== SYMBIOSIS v1.2: Consciousness Token Computation =====

def compute_symbiosis_token(eeg_window, s_t, session_prior, config, word_start_ms=None):
    """
    Compute consciousness token from EEG window and somatic state

    Master Equation:
        Token_t = H[S_t · PE_t · Φ_t · GA_t] * SE_gate

    Where:
        S_t  = Somatic state (heart-derived) [0,1]
        PE_t = Prediction error (Bayesian surprise + hierarchical)
        Φ_t  = Integrated information (consciousness proxy)
        GA_t = Global availability (gamma synchrony)
        H    = Bounding function (tanh)
        SE_gate = Spectral exponent gate (filters low-awareness)

    Args:
        eeg_window: numpy array (n_samples, n_channels) - EEG data window
        s_t: float - Somatic state from heart [0,1]
        session_prior: numpy array - Prior EEG distribution for PE computation
        config: dict - Configuration with equation thresholds
        word_start_ms: float - Optional word timestamp for logging

    Returns:
        dict with token value, components, and state classification
    """
    fs = 256  # Neurable MW75 sample rate

    # Handle 1D input
    if eeg_window.ndim == 1:
        eeg_window = eeg_window.reshape(-1, 1)

    # === PE_t: Prediction Error with Hierarchical Extension ===
    # Base PE: ||μ_post - μ_prior||^2 * Π (Gaussian approx)
    mu_post = np.mean(eeg_window, axis=0)
    mu_prior = np.mean(session_prior, axis=0) if session_prior.ndim == 2 else np.array([np.mean(session_prior)])
    var_prior = np.var(session_prior)

    pe_base = np.linalg.norm(mu_post - mu_prior) ** 2 * (1 / (var_prior + 1e-6))

    # Hierarchical PE: ∑_l PE_l (sensory → abstract)
    # l1: Delta/Theta (sensory), l2: Alpha/Beta (attention), l3: Gamma (integration)
    hier_bands = {'l1': (0.5, 8), 'l2': (8, 30), 'l3': (30, 100)}
    f, psd = welch(eeg_window.mean(axis=1), fs=fs, nperseg=min(128, len(eeg_window)))

    hier_pe = 0
    for level, (lo, hi) in hier_bands.items():
        mask = (f >= lo) & (f <= hi)
        if np.any(mask):
            # Power as proxy for prediction error (deviation from baseline)
            hier_pe += np.trapz(psd[mask], f[mask])

    pe_t = pe_base + (hier_pe / 3.0)  # Normalize hierarchical component

    # === Φ_t: Integrated Information Proxy ===
    # Approximation: det(Cov) / std^2 (captures irreducibility)
    try:
        cov = np.cov(eeg_window.T)
        cov_det = det(cov) if cov.shape[0] > 1 else cov.item()
        phi_t = abs(cov_det) / (np.std(eeg_window)**2 + 1e-6)
    except Exception as e:
        print(f"Φ computation warning: {e}")
        phi_t = 0.5  # Default neutral value

    # === GA_t: Global Availability ===
    # PLV (Phase-Locking Value) * γ_sync (gamma power ratio)

    # Phase-locking across channels
    if eeg_window.shape[1] > 1:
        phase_diff = np.angle(np.fft.fft(eeg_window[:, 1:] - eeg_window[:, :-1], axis=0))
        plv = float(np.abs(np.mean(np.exp(1j * phase_diff))))
    else:
        plv = 0.5  # Single channel default

    # Gamma synchrony (normalized gamma power)
    gamma_mask = (f >= 30) & (f <= 100)
    if np.any(gamma_mask):
        gamma_power = np.trapz(psd[gamma_mask], f[gamma_mask])
        gamma_sync = gamma_power / (np.max(psd) + 1e-6)
    else:
        gamma_sync = 0.5

    ga_t = plv * gamma_sync

    # === SE Gate: Spectral Exponent (1/f slope) ===
    # Gate = σ(SE - threshold) filters low-awareness states
    log_f = np.log(f[1:])
    log_psd = np.log(psd[1:] + 1e-10)

    if len(log_f) > 2:
        se_coeffs = np.polyfit(log_f, log_psd, 1)
        se = -se_coeffs[0]  # Negative slope (1/f^α)
        se_threshold = config.get('equations', {}).get('se_threshold', -1.5)
        se_gate = 1 / (1 + np.exp(se - se_threshold))  # Sigmoid gate
    else:
        se_gate = 1.0  # No gating if insufficient data

    # === Master Token_t = H[S_t · PE_t · Φ_t · GA_t] * SE_gate ===
    raw_token = s_t * pe_t * phi_t * ga_t * se_gate
    token = float(np.tanh(raw_token))  # Bound to [-1, 1]

    # State classification
    if token > 0.7:
        state = 'insight'  # High consciousness, flow state
    elif token > 0.4:
        state = 'flow'  # Engaged, moderate awareness
    elif token > 0:
        state = 'nominal'  # Normal awareness
    else:
        state = 'noise'  # Low-Φ, gate out

    return {
        'token': token,
        'components': {
            's_t': float(s_t),
            'pe_t': float(pe_t),
            'pe_base': float(pe_base),
            'pe_hier': float(hier_pe),
            'phi_t': float(phi_t),
            'ga_t': float(ga_t),
            'plv': float(plv),
            'gamma_sync': float(gamma_sync),
            'se_gate': float(se_gate),
            'se': float(se) if 'se' in locals() else 0
        },
        'state': state,
        'timestamp_ms': word_start_ms
    }


def compute_token_for_word(eeg_data, word, s_t, session_prior, config, fs=256):
    """
    Compute token for a specific transcribed word

    Args:
        eeg_data: Full session EEG data (n_samples, n_channels)
        word: Word dict with 'start_ms', 'end_ms', 'text'
        s_t: Current somatic state
        session_prior: Prior EEG distribution
        config: Configuration dict
        fs: Sample rate in Hz

    Returns:
        Token dict with word metadata
    """
    # Extract EEG window for word timing
    start_sample = int((word['start_ms'] / 1000) * fs)
    end_sample = int((word['end_ms'] / 1000) * fs)

    if end_sample > len(eeg_data):
        end_sample = len(eeg_data)
    if start_sample >= end_sample:
        return None

    eeg_window = eeg_data[start_sample:end_sample]

    if len(eeg_window) < 10:  # Minimum samples
        return None

    token_data = compute_symbiosis_token(
        eeg_window, s_t, session_prior, config,
        word_start_ms=word['start_ms']
    )

    # Add word metadata
    token_data['word'] = word['text']
    token_data['word_start_ms'] = word['start_ms']
    token_data['word_end_ms'] = word['end_ms']
    token_data['confidence'] = word.get('confidence', 1.0)

    return token_data
