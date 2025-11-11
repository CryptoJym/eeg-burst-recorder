#!/usr/bin/env python3
"""
Event-Triggered EEG Burst Recorder for Neurable MW75 Neuro
Records EEG bursts when signal exceeds threshold, sends LSL markers
"""
import numpy as np
import pylsl
import time
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import argparse


class EEGBurstRecorder:
    """Records EEG data bursts triggered by threshold events"""

    def __init__(
        self,
        threshold_rms: float = 50.0,
        threshold_p2p: float = 100.0,
        pre_burst_seconds: float = 1.0,
        post_burst_seconds: float = 2.0,
        output_dir: str = "burst_data",
        send_markers: bool = True,
        channel_names: Optional[List[str]] = None
    ):
        """
        Initialize burst recorder

        Args:
            threshold_rms: RMS threshold for burst detection (microvolts)
            threshold_p2p: Peak-to-peak threshold for burst detection (microvolts)
            pre_burst_seconds: Seconds of data to save before burst
            post_burst_seconds: Seconds of data to save after burst
            output_dir: Directory to save burst data
            send_markers: Whether to send LSL event markers
            channel_names: Names of EEG channels (auto-detected if None)
        """
        self.threshold_rms = threshold_rms
        self.threshold_p2p = threshold_p2p
        self.pre_burst_seconds = pre_burst_seconds
        self.post_burst_seconds = post_burst_seconds
        self.output_dir = Path(output_dir)
        self.send_markers = send_markers
        self.channel_names = channel_names

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # LSL components
        self.inlet: Optional[pylsl.StreamInlet] = None
        self.outlet: Optional[pylsl.StreamOutlet] = None
        self.sample_rate: float = 0.0
        self.n_channels: int = 0

        # Recording state
        self.buffer: List[np.ndarray] = []
        self.buffer_max_samples: int = 0
        self.burst_count: int = 0
        self.recording: bool = False
        self.last_burst_time: float = 0.0
        self.min_burst_interval: float = 3.0  # Minimum seconds between bursts

    def connect_to_stream(self, stream_type: str = 'EEG', timeout: float = 10.0) -> bool:
        """
        Connect to LSL EEG stream

        Args:
            stream_type: Type of LSL stream to look for
            timeout: Maximum seconds to wait for stream

        Returns:
            True if connected successfully
        """
        print(f"Looking for LSL stream (type='{stream_type}')...")
        streams = pylsl.resolve_byprop('type', stream_type, timeout=timeout)

        if not streams:
            print(f"❌ No {stream_type} stream found after {timeout}s")
            return False

        stream_info = streams[0]
        print(f"✓ Found stream: {stream_info.name()}")

        # Create inlet
        self.inlet = pylsl.StreamInlet(stream_info, max_buflen=360)
        self.sample_rate = stream_info.nominal_srate()
        self.n_channels = stream_info.channel_count()

        # Get channel names from stream metadata
        if self.channel_names is None:
            self.channel_names = []
            channels = stream_info.desc().child("channels").child("channel")
            for i in range(self.n_channels):
                label = channels.child_value("label")
                self.channel_names.append(label if label else f"Ch{i+1}")
                channels = channels.next_sibling()

        # Calculate buffer size
        self.buffer_max_samples = int(
            self.sample_rate * (self.pre_burst_seconds + self.post_burst_seconds + 1)
        )

        print(f"  Channels: {self.n_channels} ({', '.join(self.channel_names)})")
        print(f"  Sample rate: {self.sample_rate} Hz")
        print(f"  Buffer size: {self.buffer_max_samples} samples")

        # Create event marker outlet if needed
        if self.send_markers:
            marker_info = pylsl.StreamInfo(
                'BurstRecorder_Markers',
                'Markers',
                1,
                0,
                'string',
                'burst_recorder_001'
            )
            self.outlet = pylsl.StreamOutlet(marker_info)
            print("✓ Event marker outlet created")

        return True

    def send_marker(self, marker: str):
        """Send LSL event marker"""
        if self.outlet:
            self.outlet.push_sample([marker])
            print(f"  → Marker sent: {marker}")

    def calculate_metrics(self, data: np.ndarray) -> Dict[str, float]:
        """
        Calculate signal metrics

        Args:
            data: 2D array (samples x channels)

        Returns:
            Dictionary with RMS and P2P metrics per channel
        """
        metrics = {}

        for i, ch_name in enumerate(self.channel_names):
            channel_data = data[:, i]

            # Remove DC offset
            channel_data = channel_data - np.mean(channel_data)

            # RMS (Root Mean Square)
            rms = np.sqrt(np.mean(channel_data ** 2))

            # Peak-to-Peak
            p2p = np.max(channel_data) - np.min(channel_data)

            metrics[ch_name] = {
                'rms': rms,
                'p2p': p2p
            }

        return metrics

    def detect_burst(self, data: np.ndarray) -> Optional[Dict]:
        """
        Detect if data contains a burst event

        Args:
            data: Recent EEG data (samples x channels)

        Returns:
            Burst info dict if detected, None otherwise
        """
        # Prevent bursts too close together
        current_time = time.time()
        if current_time - self.last_burst_time < self.min_burst_interval:
            return None

        metrics = self.calculate_metrics(data)

        # Check each channel for threshold violations
        triggered_channels = []
        for ch_name, vals in metrics.items():
            if vals['rms'] > self.threshold_rms or vals['p2p'] > self.threshold_p2p:
                triggered_channels.append({
                    'channel': ch_name,
                    'rms': vals['rms'],
                    'p2p': vals['p2p']
                })

        if triggered_channels:
            return {
                'timestamp': datetime.now().isoformat(),
                'channels': triggered_channels,
                'all_metrics': metrics
            }

        return None

    def save_burst(self, data: np.ndarray, burst_info: Dict):
        """
        Save burst data to files

        Args:
            data: Burst EEG data (samples x channels)
            burst_info: Burst detection metadata
        """
        self.burst_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        burst_id = f"burst_{timestamp}_{self.burst_count:04d}"

        # Save EEG data as NPZ
        data_file = self.output_dir / f"{burst_id}.npz"
        np.savez_compressed(
            data_file,
            data=data,
            sample_rate=self.sample_rate,
            channel_names=self.channel_names,
            **burst_info
        )

        # Save metadata as JSON
        meta_file = self.output_dir / f"{burst_id}_meta.json"
        meta = {
            'burst_id': burst_id,
            'sample_rate': self.sample_rate,
            'n_samples': data.shape[0],
            'n_channels': data.shape[1],
            'channel_names': self.channel_names,
            'pre_burst_seconds': self.pre_burst_seconds,
            'post_burst_seconds': self.post_burst_seconds,
            'thresholds': {
                'rms': self.threshold_rms,
                'p2p': self.threshold_p2p
            },
            **burst_info
        }

        with open(meta_file, 'w') as f:
            json.dump(meta, f, indent=2)

        print(f"✓ Burst #{self.burst_count} saved: {burst_id}")
        print(f"  Triggered channels: {', '.join([ch['channel'] for ch in burst_info['channels']])}")

        # Send marker
        self.send_marker(f"BURST_{burst_id}")

        return burst_id

    def run(self, duration: Optional[float] = None):
        """
        Run burst recording

        Args:
            duration: Recording duration in seconds (None = infinite)
        """
        if not self.inlet:
            print("❌ Not connected to stream. Call connect_to_stream() first.")
            return

        print(f"\n{'='*60}")
        print("EEG Burst Recorder Started")
        print(f"{'='*60}")
        print(f"Thresholds: RMS={self.threshold_rms}µV, P2P={self.threshold_p2p}µV")
        print(f"Burst window: {self.pre_burst_seconds}s pre + {self.post_burst_seconds}s post")
        print(f"Output: {self.output_dir.absolute()}")
        print(f"Duration: {'∞ (press Ctrl+C to stop)' if duration is None else f'{duration}s'}")
        print(f"{'='*60}\n")

        self.recording = True
        start_time = time.time()
        samples_processed = 0

        try:
            while self.recording:
                # Check duration limit
                if duration and (time.time() - start_time) > duration:
                    print(f"\n✓ Duration limit ({duration}s) reached")
                    break

                # Pull sample
                sample, timestamp = self.inlet.pull_sample(timeout=1.0)
                if sample is None:
                    continue

                samples_processed += 1

                # Add to circular buffer
                self.buffer.append(np.array(sample))
                if len(self.buffer) > self.buffer_max_samples:
                    self.buffer.pop(0)

                # Need enough data for pre-burst window
                min_samples = int(self.sample_rate * (self.pre_burst_seconds + 0.5))
                if len(self.buffer) < min_samples:
                    continue

                # Get recent data for burst detection
                detection_window = int(self.sample_rate * 0.5)  # Last 500ms
                recent_data = np.array(self.buffer[-detection_window:])

                # Detect burst
                burst_info = self.detect_burst(recent_data)
                if burst_info:
                    # Get full burst window
                    pre_samples = int(self.sample_rate * self.pre_burst_seconds)
                    post_samples = int(self.sample_rate * self.post_burst_seconds)

                    # Wait for post-burst data
                    print(f"\n🔥 BURST DETECTED! Capturing {self.post_burst_seconds}s post-burst...")
                    for _ in range(post_samples):
                        sample, _ = self.inlet.pull_sample(timeout=1.0)
                        if sample:
                            self.buffer.append(np.array(sample))

                    # Extract burst window
                    burst_data = np.array(self.buffer[-(pre_samples + post_samples):])

                    # Save burst
                    self.save_burst(burst_data, burst_info)
                    self.last_burst_time = time.time()

                # Progress indicator
                if samples_processed % int(self.sample_rate) == 0:
                    elapsed = time.time() - start_time
                    print(f"  Recording... {elapsed:.1f}s | {samples_processed} samples | {self.burst_count} bursts", end='\r')

        except KeyboardInterrupt:
            print("\n\n✓ Recording stopped by user")

        finally:
            self.recording = False
            elapsed = time.time() - start_time
            print(f"\n{'='*60}")
            print(f"Recording Summary")
            print(f"{'='*60}")
            print(f"Duration: {elapsed:.1f}s")
            print(f"Samples processed: {samples_processed}")
            print(f"Bursts detected: {self.burst_count}")
            print(f"Output directory: {self.output_dir.absolute()}")
            print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Event-Triggered EEG Burst Recorder for Neurable MW75 Neuro'
    )
    parser.add_argument(
        '--threshold-rms',
        type=float,
        default=50.0,
        help='RMS threshold for burst detection (microvolts, default: 50.0)'
    )
    parser.add_argument(
        '--threshold-p2p',
        type=float,
        default=100.0,
        help='Peak-to-peak threshold for burst detection (microvolts, default: 100.0)'
    )
    parser.add_argument(
        '--pre-burst',
        type=float,
        default=1.0,
        help='Seconds of data to save before burst (default: 1.0)'
    )
    parser.add_argument(
        '--post-burst',
        type=float,
        default=2.0,
        help='Seconds of data to save after burst (default: 2.0)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='burst_data',
        help='Directory to save burst data (default: burst_data)'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=None,
        help='Recording duration in seconds (default: infinite)'
    )
    parser.add_argument(
        '--no-markers',
        action='store_true',
        help='Disable sending LSL event markers'
    )
    parser.add_argument(
        '--stream-type',
        type=str,
        default='EEG',
        help='LSL stream type to connect to (default: EEG)'
    )

    args = parser.parse_args()

    # Create recorder
    recorder = EEGBurstRecorder(
        threshold_rms=args.threshold_rms,
        threshold_p2p=args.threshold_p2p,
        pre_burst_seconds=args.pre_burst,
        post_burst_seconds=args.post_burst,
        output_dir=args.output_dir,
        send_markers=not args.no_markers
    )

    # Connect to stream
    if not recorder.connect_to_stream(stream_type=args.stream_type, timeout=10.0):
        print("\n❌ Failed to connect to LSL stream")
        print("Make sure Neurable Research Kit is running and streaming data")
        return 1

    # Run recording
    recorder.run(duration=args.duration)

    return 0


if __name__ == '__main__':
    exit(main())
