#!/usr/bin/env python3
"""
Real-time Spectral Analyzer
Continuous FFT analysis of EEG data with artifact awareness
"""

import numpy as np
import pylsl
from scipy import signal
from collections import deque
from datetime import datetime
import json
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpectralAnalyzer:
    """
    Performs continuous spectral analysis on EEG stream
    Calculates band powers and detects state changes
    """

    # Frequency bands (Hz)
    BANDS = {
        'delta': (0.5, 4.0),
        'theta': (4.0, 8.0),
        'alpha': (8.0, 13.0),
        'beta': (13.0, 30.0),
        'gamma': (30.0, 100.0)
    }

    def __init__(self,
                 window_seconds=2.0,
                 overlap=0.5,
                 output_interval=1.0,
                 output_file=None,
                 artifact_timestamps=None):
        """
        Args:
            window_seconds: FFT window size in seconds
            overlap: Window overlap (0.0 to 1.0)
            output_interval: How often to output band powers (seconds)
            output_file: Optional CSV file for spectral data
            artifact_timestamps: List of burst timestamps to exclude
        """
        self.window_seconds = window_seconds
        self.overlap = overlap
        self.output_interval = output_interval
        self.output_file = output_file
        self.artifact_timestamps = artifact_timestamps or []

        # Streaming state
        self.inlet = None
        self.sample_rate = None
        self.n_channels = None
        self.channel_names = None

        # Analysis buffers
        self.window_samples = None
        self.hop_samples = None
        self.buffer = None

        # Band power tracking
        self.band_powers_history = {band: deque(maxlen=60) for band in self.BANDS}
        self.last_output_time = 0

        # Output CSV
        self.csv_file = None
        self.csv_writer = None

    def connect_stream(self, stream_type='EEG', timeout=5.0):
        """Connect to LSL EEG stream"""
        logger.info(f"Looking for LSL stream (type='{stream_type}')...")

        streams = pylsl.resolve_byprop('type', stream_type, timeout=timeout)

        if not streams:
            raise RuntimeError(f"No {stream_type} stream found")

        stream_info = streams[0]
        logger.info(f"✓ Found stream: {stream_info.name()}")

        self.inlet = pylsl.StreamInlet(stream_info)
        self.sample_rate = stream_info.nominal_srate()
        self.n_channels = stream_info.channel_count()

        # Get channel names
        self.channel_names = []
        ch = stream_info.desc().child("channels").child("channel")
        for _ in range(self.n_channels):
            self.channel_names.append(ch.child_value("label"))
            ch = ch.next_sibling()

        # Calculate buffer sizes
        self.window_samples = int(self.window_seconds * self.sample_rate)
        self.hop_samples = int(self.window_samples * (1 - self.overlap))

        # Initialize circular buffer
        self.buffer = deque(maxlen=self.window_samples)

        logger.info(f"  Channels: {self.n_channels} ({', '.join(self.channel_names[:4])}...)")
        logger.info(f"  Sample rate: {self.sample_rate} Hz")
        logger.info(f"  Window: {self.window_seconds}s ({self.window_samples} samples)")
        logger.info(f"  Hop: {self.hop_samples} samples")

    def setup_output_file(self, output_path):
        """Setup CSV output file"""
        if not output_path:
            return

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.csv_file = open(output_path, 'w')

        # Write header
        header = ['timestamp', 'time_seconds']
        for band in self.BANDS:
            header.append(f'{band}_power')
        header.extend(['signal_quality', 'artifact_level'])

        self.csv_file.write(','.join(header) + '\n')
        logger.info(f"Writing spectral data to: {output_path}")

    def calculate_band_power(self, data, band_range):
        """
        Calculate power in a frequency band using Welch's method

        Args:
            data: (n_samples, n_channels) array
            band_range: (low_freq, high_freq) tuple

        Returns:
            Mean band power across channels
        """
        if len(data) < self.window_samples:
            return 0.0

        # Average across channels
        avg_signal = np.mean(data, axis=1)

        # Welch's method for power spectral density
        freqs, psd = signal.welch(
            avg_signal,
            fs=self.sample_rate,
            nperseg=min(256, len(avg_signal)),
            scaling='density'
        )

        # Find frequency range indices
        idx_band = np.logical_and(freqs >= band_range[0], freqs <= band_range[1])

        # Integrate power in band
        band_power = np.trapz(psd[idx_band], freqs[idx_band])

        return band_power

    def calculate_all_bands(self, data):
        """Calculate power for all frequency bands"""
        band_powers = {}

        for band_name, band_range in self.BANDS.items():
            power = self.calculate_band_power(data, band_range)
            band_powers[band_name] = power

        return band_powers

    def calculate_quality_metrics(self, data):
        """
        Estimate signal quality metrics

        Returns:
            dict with signal_quality and artifact_level (0-100)
        """
        if len(data) == 0:
            return {'signal_quality': 0.0, 'artifact_level': 0.0}

        # Signal quality based on variance across channels
        channel_vars = np.var(data, axis=0)
        mean_var = np.mean(channel_vars)
        var_consistency = 1.0 - (np.std(channel_vars) / (mean_var + 1e-6))
        signal_quality = max(0, min(100, var_consistency * 100))

        # Artifact level based on high-frequency content
        high_freq_power = self.calculate_band_power(data, (30.0, 100.0))
        total_power = sum(self.calculate_band_power(data, (0.5, 100.0)) for _ in range(1))
        artifact_level = min(100, (high_freq_power / (total_power + 1e-6)) * 200)

        return {
            'signal_quality': signal_quality,
            'artifact_level': artifact_level
        }

    def is_artifact_window(self, timestamp):
        """Check if current window overlaps with known artifacts"""
        window_start = timestamp - self.window_seconds
        window_end = timestamp

        for artifact_time in self.artifact_timestamps:
            if window_start <= artifact_time <= window_end:
                return True

        return False

    def normalize_band_powers(self, band_powers):
        """
        Normalize band powers to percentages (0-100)

        Makes values more intuitive for UI display
        """
        # Calculate total power
        total_power = sum(band_powers.values())

        if total_power == 0:
            return {band: 0.0 for band in band_powers}

        # Convert to percentages
        normalized = {}
        for band, power in band_powers.items():
            normalized[band] = (power / total_power) * 100

        return normalized

    def process_sample(self, sample, timestamp):
        """Process a single sample and return spectral data if ready"""
        self.buffer.append(sample)

        # Check if we have enough data and it's time to output
        current_time = time.time()
        if (len(self.buffer) >= self.window_samples and
            current_time - self.last_output_time >= self.output_interval):

            # Convert buffer to numpy array
            data = np.array(list(self.buffer))

            # Calculate band powers
            band_powers = self.calculate_all_bands(data)

            # Normalize for UI display
            normalized_powers = self.normalize_band_powers(band_powers)

            # Calculate quality metrics
            quality = self.calculate_quality_metrics(data)

            # Check for artifacts
            is_artifact = self.is_artifact_window(timestamp)

            result = {
                'timestamp': datetime.now().isoformat(),
                'time_seconds': timestamp,
                'bands': normalized_powers,
                'quality': quality,
                'is_artifact': is_artifact
            }

            # Write to CSV if enabled
            if self.csv_file:
                row = [
                    result['timestamp'],
                    f"{timestamp:.3f}",
                    f"{normalized_powers['delta']:.2f}",
                    f"{normalized_powers['theta']:.2f}",
                    f"{normalized_powers['alpha']:.2f}",
                    f"{normalized_powers['beta']:.2f}",
                    f"{normalized_powers['gamma']:.2f}",
                    f"{quality['signal_quality']:.1f}",
                    f"{quality['artifact_level']:.1f}"
                ]
                self.csv_file.write(','.join(row) + '\n')
                self.csv_file.flush()

            self.last_output_time = current_time
            return result

        return None

    def run(self, duration=None, callback=None):
        """
        Run continuous spectral analysis

        Args:
            duration: Optional duration in seconds (None = infinite)
            callback: Function to call with each spectral update
        """
        if not self.inlet:
            raise RuntimeError("Not connected to stream. Call connect_stream() first.")

        logger.info("Starting spectral analysis...")

        start_time = time.time()
        sample_count = 0

        try:
            while True:
                # Check duration limit
                elapsed = time.time() - start_time
                if duration and elapsed >= duration:
                    break

                # Pull sample from stream
                sample, timestamp = self.inlet.pull_sample(timeout=1.0)

                if sample is None:
                    continue

                sample_count += 1

                # Process sample
                result = self.process_sample(sample, elapsed)

                # Call callback if spectral data ready
                if result and callback:
                    callback(result)

                # Progress indicator
                if sample_count % 500 == 0:
                    logger.info(f"Processed {sample_count} samples ({elapsed:.1f}s)")

        except KeyboardInterrupt:
            logger.info("\nStopping spectral analysis...")

        finally:
            if self.csv_file:
                self.csv_file.close()

            logger.info(f"Processed {sample_count} samples in {elapsed:.1f}s")


def main():
    """Test spectral analyzer standalone"""
    import argparse

    parser = argparse.ArgumentParser(description='Real-time EEG Spectral Analyzer')
    parser.add_argument('--duration', type=float, default=30.0,
                       help='Duration in seconds (default: 30)')
    parser.add_argument('--output', type=str, default='spectral_output.csv',
                       help='Output CSV file')
    parser.add_argument('--window', type=float, default=2.0,
                       help='FFT window size in seconds')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Output interval in seconds')

    args = parser.parse_args()

    analyzer = SpectralAnalyzer(
        window_seconds=args.window,
        output_interval=args.interval
    )

    # Connect to stream
    analyzer.connect_stream()

    # Setup output
    analyzer.setup_output_file(args.output)

    # Callback to print results
    def print_result(result):
        bands = result['bands']
        print(f"\r[{result['time_seconds']:6.1f}s] "
              f"Delta: {bands['delta']:5.1f}% | "
              f"Theta: {bands['theta']:5.1f}% | "
              f"Alpha: {bands['alpha']:5.1f}% | "
              f"Beta: {bands['beta']:5.1f}% | "
              f"Gamma: {bands['gamma']:5.1f}%",
              end='', flush=True)

    # Run analysis
    analyzer.run(duration=args.duration, callback=print_result)

    print(f"\n\nSpectral data saved to: {args.output}")


if __name__ == '__main__':
    main()
