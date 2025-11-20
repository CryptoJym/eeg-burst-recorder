"""
Test Suite for Agent 3 (Cross-Modal Neuroscience) - Production Grade

This test suite uses SYNTHETIC SIGNALS to verify the mathematical correctness
of the signal processing algorithms (PAC, Envelope Tracking, Coherence).

We generate known signals (e.g., sine waves) where we know the ground truth,
and assert that the analyzer recovers these relationships.
"""

import unittest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cross_modal import CrossModalAnalyzer

class TestCrossModalAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.fs_eeg = 256
        self.fs_audio = 16000
        self.analyzer = CrossModalAnalyzer(fs_eeg=self.fs_eeg, fs_audio=self.fs_audio)
        
    def generate_pac_signal(self, duration_sec=5, coupling_strength=0.8):
        """
        Generate a synthetic signal with Phase-Amplitude Coupling.
        Theta phase (6Hz) modulates Gamma amplitude (40Hz).
        """
        t = np.linspace(0, duration_sec, int(duration_sec * self.fs_eeg))
        
        # Theta wave (Phase)
        theta_phase = 2 * np.pi * 6 * t
        theta = np.sin(theta_phase)
        
        # Gamma wave (Amplitude) modulated by Theta
        # Amplitude varies between (1-strength) and (1+strength) based on Theta phase
        modulation = (1 - coupling_strength) + coupling_strength * (theta + 1) / 2
        gamma = np.sin(2 * np.pi * 40 * t) * modulation
        
        # Combined signal + noise
        signal = theta + gamma + 0.1 * np.random.randn(len(t))
        return signal

    def test_pac_detection_strong_coupling(self):
        """Test that PAC detects strong coupling in a synthetic signal."""
        # Generate signal with strong coupling (0.8)
        signal = self.generate_pac_signal(coupling_strength=0.8)
        
        # Compute PAC
        mi = self.analyzer.compute_pac(signal, phase_band=(4, 8), amp_band=(30, 80))
        
        # Expect high Modulation Index (typically > 0.01 for this simple synthetic case, 
        # but real MI values are small. For this clean signal, it should be significant)
        print(f"Computed MI (Strong): {mi}")
        self.assertGreater(mi, 0.005, "Failed to detect strong Phase-Amplitude Coupling")

    def test_pac_detection_no_coupling(self):
        """Test that PAC is low for uncoupled signals."""
        t = np.linspace(0, 5, int(5 * self.fs_eeg))
        # Independent Theta and Gamma
        theta = np.sin(2 * np.pi * 6 * t)
        gamma = np.sin(2 * np.pi * 40 * t) # Constant amplitude
        signal = theta + gamma + 0.1 * np.random.randn(len(t))
        
        mi = self.analyzer.compute_pac(signal, phase_band=(4, 8), amp_band=(30, 80))
        
        print(f"Computed MI (None): {mi}")
        self.assertLess(mi, 0.005, "False positive PAC detected in uncoupled signal")

    def test_speech_envelope_tracking(self):
        """Test that the speech envelope is correctly extracted and resampled."""
        duration = 2.0
        t_audio = np.linspace(0, duration, int(duration * self.fs_audio))
        
        # Synthetic speech: 5Hz amplitude modulation (syllable rate) on 1000Hz carrier
        envelope_freq = 5
        carrier_freq = 1000
        
        true_envelope = 0.5 * (1 + np.sin(2 * np.pi * envelope_freq * t_audio))
        audio = true_envelope * np.sin(2 * np.pi * carrier_freq * t_audio)
        
        # Extract envelope
        extracted_env = self.analyzer.track_speech_envelope(audio)
        
        # Check length (should match EEG fs)
        expected_len = int(duration * self.fs_eeg)
        self.assertEqual(len(extracted_env), expected_len, "Resampled envelope length incorrect")
        
        # Check frequency content of extracted envelope
        # It should have a peak at 5Hz
        from scipy.signal import welch
        f, Pxx = welch(extracted_env, fs=self.fs_eeg, nperseg=256)
        peak_freq = f[np.argmax(Pxx)]
        
        # Allow small margin of error due to resolution
        self.assertTrue(4 <= peak_freq <= 6, f"Envelope frequency {peak_freq}Hz not matching input 5Hz")

    def test_audio_eeg_coherence(self):
        """Test coherence between correlated audio envelope and EEG."""
        duration = 5.0
        t_eeg = np.linspace(0, duration, int(duration * self.fs_eeg))
        
        # Shared signal (the "speech envelope" driving the brain)
        shared_drive = np.sin(2 * np.pi * 5 * t_eeg) # 5Hz Theta rhythm
        
        # Audio envelope (perfectly correlated)
        audio_env = shared_drive
        
        # EEG (correlated + noise)
        eeg_data = shared_drive + 0.5 * np.random.randn(len(t_eeg))
        
        # Compute coherence
        coh = self.analyzer.compute_audio_eeg_coherence(audio_env, eeg_data)
        
        print(f"Computed Coherence: {coh}")
        self.assertGreater(coh, 0.5, "Failed to detect high coherence in correlated signals")

    def test_analyze_session_integration(self):
        """Test the full analysis pipeline."""
        # Create dummy data
        duration = 2.0
        eeg_data = np.random.randn(int(duration * self.fs_eeg))
        audio_data = np.random.randn(int(duration * self.fs_audio))
        
        channels = {'AF7': eeg_data, 'AF8': eeg_data}
        
        results = self.analyzer.analyze_session(channels, audio_data)
        
        self.assertIn('pac_theta_gamma', results)
        self.assertIn('speech_tracking_coherence', results)
        self.assertIn('AF7', results['pac_theta_gamma'])
        self.assertIsInstance(results['pac_theta_gamma']['AF7'], float)

if __name__ == '__main__':
    unittest.main()
