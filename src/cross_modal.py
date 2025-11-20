"""
Agent 3: Cross-Modal Neuroscience Analyzer (Production Grade)

This module implements advanced signal processing to link EEG and Audio data.
It uses real mathematical transforms (Hilbert, Coherence) to quantify:
1. Phase-Amplitude Coupling (PAC): How theta phase modulates gamma amplitude.
2. Speech Envelope Tracking: How well EEG tracks the speech audio envelope.
3. Audio-EEG Coherence: Spectral synchronization between brain and voice.

Dependencies: numpy, scipy
"""

import numpy as np
from scipy.signal import hilbert, coherence, butter, filtfilt
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CrossModalAnalyzer")

class CrossModalAnalyzer:
    def __init__(self, fs_eeg: float = 256.0, fs_audio: float = 16000.0):
        """
        Initialize the analyzer with sampling rates.
        
        Args:
            fs_eeg: EEG sampling rate in Hz (default 256)
            fs_audio: Audio sampling rate in Hz (default 16000)
        """
        self.fs_eeg = fs_eeg
        self.fs_audio = fs_audio
        
    def _bandpass_filter(self, data: np.ndarray, lowcut: float, highcut: float, fs: float, order: int = 4) -> np.ndarray:
        """Apply a Butterworth bandpass filter."""
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        return filtfilt(b, a, data)

    def compute_pac(self, eeg_data: np.ndarray, phase_band: Tuple[float, float] = (4, 8), amp_band: Tuple[float, float] = (30, 80)) -> float:
        """
        Compute Phase-Amplitude Coupling (PAC) using the Modulation Index (MI).
        Measures how the phase of low-frequency oscillations modulates the amplitude of high-frequency oscillations.
        
        Args:
            eeg_data: 1D numpy array of EEG data
            phase_band: Tuple of (low, high) Hz for the phase signal (e.g., Theta 4-8Hz)
            amp_band: Tuple of (low, high) Hz for the amplitude signal (e.g., Gamma 30-80Hz)
            
        Returns:
            Modulation Index (float) between 0.0 (no coupling) and 1.0 (perfect coupling)
        """
        if len(eeg_data) < self.fs_eeg:
            logger.warning("Data too short for PAC computation")
            return 0.0
            
        try:
            # 1. Extract Phase Signal (Low Frequency)
            phase_sig = self._bandpass_filter(eeg_data, phase_band[0], phase_band[1], self.fs_eeg)
            phase_analytic = hilbert(phase_sig)
            phases = np.angle(phase_analytic)
            
            # 2. Extract Amplitude Signal (High Frequency)
            amp_sig = self._bandpass_filter(eeg_data, amp_band[0], amp_band[1], self.fs_eeg)
            amp_analytic = hilbert(amp_sig)
            amplitudes = np.abs(amp_analytic)
            
            # 3. Bin phases and compute mean amplitude per bin
            n_bins = 18
            bin_edges = np.linspace(-np.pi, np.pi, n_bins + 1)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            mean_amps = np.zeros(n_bins)
            for i in range(n_bins):
                idx = np.where((phases >= bin_edges[i]) & (phases < bin_edges[i+1]))[0]
                if len(idx) > 0:
                    mean_amps[i] = np.mean(amplitudes[idx])
            
            # Normalize probability distribution
            p = mean_amps / np.sum(mean_amps)
            
            # 4. Compute Kullback-Leibler divergence from uniform distribution
            # Uniform distribution q = 1/N
            q = 1.0 / n_bins
            kl_divergence = np.sum(p * np.log(p / q + 1e-12))
            
            # 5. Modulation Index
            mi = kl_divergence / np.log(n_bins)
            return float(mi)
            
        except Exception as e:
            logger.error(f"Error computing PAC: {e}")
            return 0.0

    def track_speech_envelope(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Extract the amplitude envelope of the speech signal.
        This represents the rhythm of speech (syllables/words).
        
        Args:
            audio_data: 1D numpy array of audio data
            
        Returns:
            Envelope signal (resampled to match EEG sampling rate if needed)
        """
        try:
            # 1. Compute Hilbert envelope
            analytic_signal = hilbert(audio_data)
            envelope = np.abs(analytic_signal)
            
            # 2. Low-pass filter to get the broad envelope (speech rhythm < 20Hz)
            # Using 20Hz as cutoff for speech envelope
            b, a = butter(4, 20 / (0.5 * self.fs_audio), btype='low')
            smoothed_env = filtfilt(b, a, envelope)
            
            # 3. Resample to EEG rate if necessary
            if self.fs_audio != self.fs_eeg:
                # Calculate number of samples
                num_samples = int(len(smoothed_env) * self.fs_eeg / self.fs_audio)
                from scipy.signal import resample
                resampled_env = resample(smoothed_env, num_samples)
                return resampled_env
            
            return smoothed_env
            
        except Exception as e:
            logger.error(f"Error tracking speech envelope: {e}")
            return np.zeros(int(len(audio_data) * self.fs_eeg / self.fs_audio))

    def compute_audio_eeg_coherence(self, audio_env: np.ndarray, eeg_data: np.ndarray) -> float:
        """
        Compute the spectral coherence between the speech envelope and EEG signal.
        High coherence in Theta band (4-8Hz) indicates neural tracking of speech.
        
        Args:
            audio_env: Speech envelope (must be same sampling rate as EEG)
            eeg_data: EEG data (1D array)
            
        Returns:
            Mean coherence in the Theta band (4-8Hz)
        """
        # Ensure lengths match
        min_len = min(len(audio_env), len(eeg_data))
        x = audio_env[:min_len]
        y = eeg_data[:min_len]
        
        if min_len < self.fs_eeg: # Need at least 1 second
             return 0.0

        try:
            # Compute Magnitude Squared Coherence
            f, Cxy = coherence(x, y, fs=self.fs_eeg, nperseg=min(256, min_len//2))
            
            # Average coherence in Theta band (4-8 Hz)
            theta_idx = np.where((f >= 4) & (f <= 8))[0]
            if len(theta_idx) > 0:
                mean_coherence = np.mean(Cxy[theta_idx])
                return float(mean_coherence)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error computing coherence: {e}")
            return 0.0

    def analyze_session(self, eeg_channels: Dict[str, np.ndarray], audio_data: np.ndarray) -> Dict:
        """
        Perform full cross-modal analysis on a session segment.
        
        Args:
            eeg_channels: Dict of channel_name -> numpy array
            audio_data: Numpy array of audio
            
        Returns:
            Dictionary of metrics
        """
        results = {
            "pac_theta_gamma": {},
            "speech_tracking_coherence": {}
        }
        
        # 1. Process Audio Envelope
        speech_env = self.track_speech_envelope(audio_data)
        
        # 2. Analyze each EEG channel
        for ch_name, eeg_data in eeg_channels.items():
            # PAC
            pac = self.compute_pac(eeg_data)
            results["pac_theta_gamma"][ch_name] = pac
            
            # Speech Tracking (Coherence)
            coh = self.compute_audio_eeg_coherence(speech_env, eeg_data)
            results["speech_tracking_coherence"][ch_name] = coh
            
        return results
