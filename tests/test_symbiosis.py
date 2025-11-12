#!/usr/bin/env python3
"""
Symbiosis Pipeline Tests

Tests for timestamp alignment, transcription, token computation, and fusion.
"""

import unittest
import numpy as np
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.timestamp_aligner import TimestampAligner
from src.analyzer import compute_symbiosis_token
from src.heart_sync import HeartSyncer


class TestTimestampAligner(unittest.TestCase):
    """Test timestamp synchronization"""

    def test_aligner_initialization(self):
        """Test aligner creates consistent baseline"""
        aligner = TimestampAligner()
        self.assertIsNotNone(aligner.base_ns)
        self.assertGreater(aligner.base_ns, 0)

    def test_jitter_calculation(self):
        """Test jitter calculation with mock timestamps"""
        aligner = TimestampAligner()

        # Simulate 100 alignment checks
        for _ in range(100):
            audio_ms = aligner.stamp_ms()
            eeg_ms = audio_ms + np.random.uniform(-2, 2)  # Simulate <2ms jitter
            jitter = aligner.align_jitter(audio_ms, eeg_ms)
            self.assertLess(jitter, 5)  # Target <5ms

        stats = aligner.get_jitter_stats()
        self.assertEqual(stats['count'], 100)
        self.assertLess(stats['mean'], 5)
        print(f"✓ Jitter test: mean={stats['mean']:.2f}ms, max={stats['max']:.2f}ms")


class TestSymbiosisToken(unittest.TestCase):
    """Test consciousness token computation"""

    def test_token_computation(self):
        """Test token computation with mock EEG data"""
        # Mock EEG window (256 samples, 14 channels)
        eeg_window = np.random.randn(256, 14) * 10  # μV scale
        session_prior = np.random.randn(1000, 14) * 10

        # Mock somatic state
        s_t = 0.6

        # Mock config
        config = {'equations': {'se_threshold': -1.5}}

        token_data = compute_symbiosis_token(
            eeg_window, s_t, session_prior, config
        )

        # Validate token structure
        self.assertIn('token', token_data)
        self.assertIn('components', token_data)
        self.assertIn('state', token_data)

        # Validate token bounds
        self.assertLessEqual(token_data['token'], 1.0)
        self.assertGreaterEqual(token_data['token'], -1.0)

        # Validate components
        components = token_data['components']
        self.assertIn('s_t', components)
        self.assertIn('pe_t', components)
        self.assertIn('phi_t', components)
        self.assertIn('ga_t', components)
        self.assertIn('se_gate', components)

        # SE gate should be in [0,1]
        self.assertLessEqual(components['se_gate'], 1.0)
        self.assertGreaterEqual(components['se_gate'], 0.0)

        print(f"✓ Token: {token_data['token']:.3f} ({token_data['state']})")
        print(f"  Components: S_t={components['s_t']:.2f}, PE_t={components['pe_t']:.2f}, "
              f"Φ_t={components['phi_t']:.2f}, GA_t={components['ga_t']:.2f}")


class TestHeartSync(unittest.TestCase):
    """Test heart monitoring integration"""

    def test_somatic_state_computation(self):
        """Test S_t computation from heart signals"""
        config = {'heart': {'poll_interval': 5}}
        heart = HeartSyncer(config)

        # Test various HRV/GSR combinations
        test_cases = [
            (0.5, 0.5, "neutral"),
            (0.8, 0.7, "high arousal"),
            (0.2, 0.3, "low arousal")
        ]

        for hrv, gsr, desc in test_cases:
            s_t = heart.compute_s_t(hrv, gsr)
            self.assertGreaterEqual(s_t, 0.0)
            self.assertLessEqual(s_t, 1.0)
            print(f"✓ S_t({desc}): HRV={hrv}, GSR={gsr} → S_t={s_t:.3f}")


class TestSymbiosisFusion(unittest.TestCase):
    """Test multi-modal fusion"""

    def test_word_token_fusion(self):
        """Test token computation for transcribed word"""
        # Mock full session EEG (10s at 256Hz)
        eeg_data = np.random.randn(2560, 14) * 10
        session_prior = eeg_data[:1000]

        # Mock word
        word = {
            'text': 'insight',
            'start_ms': 2000,
            'end_ms': 2500,
            'confidence': 0.95
        }

        # Mock somatic state
        s_t = 0.7

        # Config
        config = {'equations': {'se_threshold': -1.5}}

        # Compute token for word
        from src.analyzer import compute_token_for_word
        token_data = compute_token_for_word(eeg_data, word, s_t, session_prior, config)

        self.assertIsNotNone(token_data)
        self.assertEqual(token_data['word'], 'insight')
        self.assertLessEqual(abs(token_data['token']), 1.0)

        print(f"✓ Word '{word['text']}' @ {word['start_ms']}ms → "
              f"Token={token_data['token']:.3f} ({token_data['state']})")


if __name__ == '__main__':
    unittest.main()
