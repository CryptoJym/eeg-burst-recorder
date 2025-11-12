#!/usr/bin/env python3
"""
Event-Triggered EEG Burst Recorder for Neurable MW75 Neuro
Records EEG bursts when signal exceeds threshold, sends LSL markers

MindMeld Edition: Adds audio sync, Grok JSON export, and ML state analysis
"""
import numpy as np
import pylsl
import time
import json
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import argparse

# MindMeld imports
try:
    from src.audio_sync import AudioLSLSync
    from src.grok_exporter import GrokExport
except ImportError:
    AudioLSLSync = None
    GrokExport = None
    print("Warning: MindMeld features not available (missing src modules)")


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
        channel_names: Optional[List[str]] = None,
        config_file: Optional[str] = None,
        enable_audio: bool = False,
        mode: str = 'burst'
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
            config_file: Path to YAML config (for MindMeld mode)
            enable_audio: Enable audio-LSL sync
            mode: 'burst' or 'continuous' recording mode
        """
        # Load config if provided
        self.config = {}
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            # Override thresholds from config
            threshold_rms = self.config.get('thresholds', {}).get('rms', threshold_rms)
            threshold_p2p = self.config.get('thresholds', {}).get('p2p', threshold_p2p)

        self.threshold_rms = threshold_rms
        self.threshold_p2p = threshold_p2p
        self.pre_burst_seconds = pre_burst_seconds
        self.post_burst_seconds = post_burst_seconds
        self.output_dir = Path(output_dir)
        self.send_markers = send_markers
        self.channel_names = channel_names
        self.mode = mode
        self.chunk_duration = 30.0 if mode == 'continuous' else None

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # MindMeld: Audio sync
        self.audio_sync = None
        self.enable_audio = enable_audio and AudioLSLSync is not None
        if self.enable_audio:
            audio_config = self.config.get('audio', {'enable': True, 'sample_rate': 44100, 'lsl_stream_name': 'Audio'})
            try:
                self.audio_sync = AudioLSLSync(audio_config)
                print("✓ MindMeld: Audio sync enabled")
            except Exception as e:
                print(f"Warning: Audio sync failed to initialize: {e}")
                self.enable_audio = False

        # MindMeld: Grok exporter
        self.exporter = GrokExport() if GrokExport else None
        if self.exporter:
            print("✓ MindMeld: Grok exporter enabled")

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
        self.time_since_last_chunk: float = 0.0  # For continuous mode

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
        Save burst data to files (MindMeld enhanced)

        Args:
            data: Burst EEG data (samples x channels)
            burst_info: Burst detection metadata
        """
        self.burst_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        burst_id = f"burst_{timestamp}_{self.burst_count:04d}"

        # MindMeld: Capture audio if enabled
        audio_data = None
        if self.enable_audio and self.audio_sync:
            try:
                trigger_ms = time.time() * 1000
                audio_data = self.audio_sync.capture(
                    trigger_ms - (self.pre_burst_seconds * 1000),
                    self.pre_burst_seconds + self.post_burst_seconds
                )
            except Exception as e:
                print(f"  Warning: Audio capture failed: {e}")

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

        # MindMeld: Grok export with ML analysis
        if self.exporter:
            try:
                insights = self.exporter.quick_analyze(data, self.sample_rate, self.n_channels)
                payload = {
                    'burst_id': burst_id,
                    'eeg': {
                        'data': data.tolist(),
                        'sample_rate': self.sample_rate,
                        'channels': self.channel_names,
                        'metrics': burst_info.get('all_metrics', {})
                    },
                    'audio': audio_data,
                    'timestamp': burst_info.get('timestamp'),
                    'thresholds': {'rms': self.threshold_rms, 'p2p': self.threshold_p2p},
                    'tags': self.config.get('tags', []),
                    'insights': insights
                }
                grok_file = self.output_dir / f"{burst_id}.json.snappy"
                self.exporter.dump(payload, str(grok_file))
            except Exception as e:
                print(f"  Warning: Grok export failed: {e}")

        print(f"✓ Burst #{self.burst_count} saved: {burst_id}")
        print(f"  Triggered channels: {', '.join([ch['channel'] for ch in burst_info['channels']])}")

        # Send marker
        self.send_marker(f"BURST_{burst_id}")

        return burst_id

    def record_chunk(self, start_time: float):
        """
        Record a fixed-duration chunk (continuous mode)

        Args:
            start_time: Timestamp when chunk started
        """
        duration = self.chunk_duration
        if not duration:
            return

        # Get chunk data from buffer
        chunk_samples = int(self.sample_rate * duration)
        if len(self.buffer) < chunk_samples:
            return  # Not enough data yet

        chunk_data = np.array(self.buffer[-chunk_samples:])

        # Create chunk ID
        self.burst_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chunk_id = f"chunk_{timestamp}_{self.burst_count:04d}"

        # Calculate metrics
        all_metrics = self.calculate_metrics(chunk_data)

        # MindMeld: Capture audio
        audio_data = None
        if self.enable_audio and self.audio_sync:
            try:
                audio_data = self.audio_sync.capture(start_time * 1000, duration)
            except Exception as e:
                print(f"  Warning: Audio capture failed: {e}")

        # MindMeld: Grok export with ML analysis
        if self.exporter:
            try:
                insights = self.exporter.quick_analyze(chunk_data, self.sample_rate, self.n_channels)
                payload = {
                    'burst_id': chunk_id,
                    'type': 'chunk',
                    'eeg': {
                        'data': chunk_data.tolist(),
                        'sample_rate': self.sample_rate,
                        'channels': self.channel_names,
                        'metrics': all_metrics
                    },
                    'audio': audio_data,
                    'timestamp': datetime.now().isoformat(),
                    'duration': duration,
                    'thresholds': {'rms': self.threshold_rms, 'p2p': self.threshold_p2p},
                    'tags': self.config.get('tags', []) + ['talk_mode', 'continuous'],
                    'insights': insights
                }
                grok_file = self.output_dir / f"{chunk_id}.json.snappy"
                self.exporter.dump(payload, str(grok_file))
                print(f"✓ Chunk #{self.burst_count} saved: {chunk_id} (state: {insights.get('state', 'unknown')})")
            except Exception as e:
                print(f"  Warning: Chunk export failed: {e}")

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
        print(f"EEG {'MindMeld ' if self.exporter else ''}Burst Recorder Started")
        print(f"{'='*60}")
        print(f"Mode: {self.mode.upper()}")
        if self.mode == 'burst':
            print(f"Thresholds: RMS={self.threshold_rms}µV, P2P={self.threshold_p2p}µV")
            print(f"Burst window: {self.pre_burst_seconds}s pre + {self.post_burst_seconds}s post")
        else:
            print(f"Chunk duration: {self.chunk_duration}s")
        print(f"Audio sync: {'✓ Enabled' if self.enable_audio else '✗ Disabled'}")
        print(f"Grok export: {'✓ Enabled' if self.exporter else '✗ Disabled'}")
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

                # Mode-specific handling
                if self.mode == 'burst':
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

                elif self.mode == 'continuous':
                    # Check if it's time for a new chunk
                    elapsed = time.time() - start_time
                    if elapsed - self.time_since_last_chunk >= self.chunk_duration:
                        self.record_chunk(start_time + self.time_since_last_chunk)
                        self.time_since_last_chunk = elapsed

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
    # MindMeld arguments
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to YAML config file (e.g., config/meditation.yaml)'
    )
    parser.add_argument(
        '--enable-audio',
        action='store_true',
        help='Enable audio-LSL synchronization for MindMeld'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['burst', 'continuous'],
        default='burst',
        help='Recording mode: burst (threshold-triggered) or continuous (fixed chunks)'
    )

    args = parser.parse_args()

    # Create recorder
    recorder = EEGBurstRecorder(
        threshold_rms=args.threshold_rms,
        threshold_p2p=args.threshold_p2p,
        pre_burst_seconds=args.pre_burst,
        post_burst_seconds=args.post_burst,
        output_dir=args.output_dir,
        send_markers=not args.no_markers,
        config_file=args.config,
        enable_audio=args.enable_audio,
        mode=args.mode
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
