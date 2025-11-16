"""
Multi-modal Speaking Detection using Audio + EEG + HRV

This module implements speaking vs listening detection to prevent false
low-consciousness readings during speech, which suppresses gamma and
creates EEG artifacts from jaw movement.

The detector uses three independent signals:
1. Audio amplitude (high during speaking)
2. Beta/gamma ratio (speaking suppresses gamma)
3. HRV drop (speaking increases arousal)

Requires ≥2 signals to agree OR very strong audio alone to avoid false positives.
Applies temporal smoothing to filter brief sounds.
"""

import numpy as np
from typing import Dict, Tuple, List


class SpeakingDetector:
    """Multi-modal speaking detection using audio + EEG + HRV"""

    def __init__(self, config: Dict):
        """
        Initialize speaking detector with configurable thresholds.

        Args:
            config: Configuration dict with optional keys:
                - audio_threshold: Amplitude threshold for speaking (default: 0.02)
                - beta_gamma_threshold: Beta/gamma ratio threshold (default: 2.0)
                - hrv_drop_threshold: HRV drop ratio threshold (default: 0.15)
                - speaking_window_sec: Time window for smoothing (default: 2.0)
                - min_speaking_sec: Minimum sustained duration (default: 0.5)
        """
        self.audio_threshold = config.get('audio_threshold', 0.02)
        self.beta_gamma_threshold = config.get('beta_gamma_threshold', 2.0)
        self.hrv_drop_threshold = config.get('hrv_drop_threshold', 0.15)
        self.window_duration = config.get('speaking_window_sec', 2.0)
        self.min_speaking_duration = config.get('min_speaking_sec', 0.5)

        # Track recent detections for temporal smoothing
        self.recent_detections: List[Dict] = []

    def detect(self, audio_amplitude: float, beta_power: float,
               gamma_power: float, hrv: float, hrv_baseline: float,
               timestamp: float) -> Tuple[bool, float]:
        """
        Detect speaking using multi-modal inputs.

        Args:
            audio_amplitude: RMS audio amplitude (normalized)
            beta_power: EEG beta band power
            gamma_power: EEG gamma band power
            hrv: Current heart rate variability
            hrv_baseline: Baseline HRV for comparison
            timestamp: Current timestamp in seconds

        Returns:
            Tuple of (is_speaking: bool, confidence: float in [0, 1])
        """

        # Signal 1: Audio amplitude
        audio_active = audio_amplitude > self.audio_threshold
        audio_confidence = min(audio_amplitude / (self.audio_threshold * 2), 1.0)

        # Signal 2: Beta/Gamma ratio (speaking suppresses gamma)
        # Use epsilon to avoid division by zero
        beta_gamma_ratio = beta_power / (gamma_power + 1e-6)
        eeg_speaking = beta_gamma_ratio > self.beta_gamma_threshold
        eeg_confidence = min(beta_gamma_ratio / (self.beta_gamma_threshold * 2), 1.0)

        # Signal 3: HRV drop (speaking increases arousal/reduces relaxation)
        # High HRV = relaxation (parasympathetic), Low HRV = stress (sympathetic)
        hrv_drop = (hrv_baseline - hrv) / (hrv_baseline + 1e-6)
        hrv_speaking = hrv_drop > self.hrv_drop_threshold
        hrv_confidence = min(hrv_drop / (self.hrv_drop_threshold * 2), 1.0)

        # Combined confidence: weighted average of three signals
        # Audio is most reliable during speaking, EEG suppression is physiological,
        # HRV drop indicates arousal shift
        confidence = 0.5 * audio_confidence + 0.3 * eeg_confidence + 0.2 * hrv_confidence

        # Decision logic:
        # - Require ≥2 signals to agree (prevent false positives from single signal)
        # - OR strong audio (>2x threshold) alone can trigger
        signals_agree = sum([audio_active, eeg_speaking, hrv_speaking]) >= 2
        strong_audio = audio_amplitude > (self.audio_threshold * 2.0)
        is_speaking = signals_agree or strong_audio

        # Store detection for temporal smoothing
        self.recent_detections.append({
            'timestamp': timestamp,
            'is_speaking': is_speaking,
            'confidence': confidence
        })

        # Remove old detections outside the window
        self.recent_detections = [
            d for d in self.recent_detections
            if timestamp - d['timestamp'] <= self.window_duration
        ]

        # Temporal smoothing: require minimum sustained duration
        # This filters brief sounds (coughs, clicks, etc.)
        if len(self.recent_detections) >= 2:
            # Calculate time span of recent detections
            time_span = self.recent_detections[-1]['timestamp'] - self.recent_detections[0]['timestamp']

            # Count speaking detections in window
            speaking_count = sum(1 for d in self.recent_detections if d['is_speaking'])

            # If time span is good, estimate duration of speaking
            if time_span > 0:
                speaking_duration = speaking_count * (time_span / len(self.recent_detections))

                # If speaking is too brief, suppress it
                if speaking_duration < self.min_speaking_duration:
                    is_speaking = False
                    confidence *= 0.5  # Reduce confidence for unsustained signal

        return is_speaking, confidence


def integrate_speaking_detection(timeline_item: Dict, is_speaking: bool) -> Dict:
    """
    Integrate speaking detection into consciousness token timeline.

    When speaking is detected, adjust GA_t (global workspace access) because
    speaking is a form of global workspace engagement (motor cortex activation,
    executive control).

    Args:
        timeline_item: Timeline item dict with keys like 'GA_t', 'token', etc.
        is_speaking: Boolean from SpeakingDetector.detect()

    Returns:
        Modified timeline_item with 'speaking' and 'speaking_adjusted' flags
    """
    if is_speaking:
        timeline_item['speaking'] = True
        timeline_item['speaking_adjusted'] = True
        # Boost GA_t (speaking is global workspace engagement)
        # Cap at 1.0 to maintain valid range [0, 1]
        timeline_item['GA_t'] = min(timeline_item.get('GA_t', 0.5) * 1.2, 1.0)
    else:
        timeline_item['speaking'] = False
        timeline_item['speaking_adjusted'] = False

    return timeline_item
