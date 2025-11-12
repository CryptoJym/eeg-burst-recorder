#!/usr/bin/env python3
"""
Timestamp Aligner - LSL-Free Synchronization
Uses perf_counter_ns() for monotonic session clock with <5ms jitter target
"""

import time
import logging

logger = logging.getLogger(__name__)


class TimestampAligner:
    """High-precision timestamp alignment for EEG/Audio/Heart synchronization"""

    def __init__(self):
        self.base_ns = time.perf_counter_ns()  # Monotonic session zero
        self.jitter_log = []  # Track alignment quality
        logger.info(f"TimestampAligner initialized at {self.base_ns}ns")

    def stamp_ms(self):
        """Get current timestamp in milliseconds from session start"""
        return (time.perf_counter_ns() - self.base_ns) / 1_000_000  # ms precision

    def stamp_ns(self):
        """Get current timestamp in nanoseconds from session start"""
        return time.perf_counter_ns() - self.base_ns

    def align_jitter(self, audio_ms, eeg_ms):
        """
        Calculate jitter between audio and EEG timestamps

        Args:
            audio_ms: Audio timestamp in milliseconds
            eeg_ms: EEG timestamp in milliseconds

        Returns:
            float: Absolute jitter in milliseconds
        """
        jitter = abs(audio_ms - eeg_ms)
        self.jitter_log.append(jitter)

        if jitter > 10:
            logger.warning(f"High jitter detected: {jitter:.2f}ms")

        return jitter

    def get_jitter_stats(self):
        """Get statistics on alignment jitter"""
        if not self.jitter_log:
            return {'mean': 0, 'max': 0, 'count': 0}

        return {
            'mean': sum(self.jitter_log) / len(self.jitter_log),
            'max': max(self.jitter_log),
            'min': min(self.jitter_log),
            'count': len(self.jitter_log)
        }

    def reset(self):
        """Reset the session clock"""
        self.base_ns = time.perf_counter_ns()
        self.jitter_log = []
        logger.info("TimestampAligner reset")
