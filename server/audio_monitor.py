#!/usr/bin/env python3
"""
Audio Monitor for Real-time Audio LSL Stream
Captures audio from LSL Audio stream and provides waveform data for visualization
"""

import numpy as np
import time
import logging
from typing import Optional, Callable, Dict, List
from pylsl import StreamInlet, resolve_byprop

logger = logging.getLogger(__name__)


class AudioMonitor:
    """Monitor LSL Audio stream and provide real-time audio data"""

    def __init__(
        self,
        stream_name: str = 'Audio',
        window_seconds: float = 1.0,
        update_interval: float = 0.1
    ):
        """
        Initialize audio monitor

        Args:
            stream_name: LSL stream name to connect to
            window_seconds: Sliding window size in seconds for display
            update_interval: How often to emit audio updates (seconds)
        """
        self.stream_name = stream_name
        self.window_seconds = window_seconds
        self.update_interval = update_interval

        self.inlet: Optional[StreamInlet] = None
        self.sample_rate: Optional[float] = None
        self.n_channels: int = 1

        # Rolling buffer for audio data
        self.audio_buffer: List[np.ndarray] = []
        self.timestamp_buffer: List[float] = []
        self.max_buffer_samples: int = 0

        # Timing
        self.last_update_time: float = 0

        logger.info(f"AudioMonitor initialized: window={window_seconds}s, interval={update_interval}s")

    def connect_stream(self, timeout: float = 10.0) -> bool:
        """
        Connect to LSL Audio stream

        Args:
            timeout: Max seconds to wait for stream

        Returns:
            True if connected successfully
        """
        logger.info(f"Searching for LSL Audio stream: {self.stream_name}")

        try:
            streams = resolve_byprop('type', 'Audio', minimum=0, timeout=timeout)

            if not streams:
                logger.warning(f"No Audio stream found after {timeout}s")
                return False

            # Connect to first audio stream
            stream_info = streams[0]
            self.inlet = StreamInlet(stream_info, max_chunklen=1024)

            # Get stream info
            self.sample_rate = stream_info.nominal_srate()
            self.n_channels = stream_info.channel_count()

            # Calculate buffer size
            self.max_buffer_samples = int(self.sample_rate * self.window_seconds)

            logger.info(f"✓ Connected to Audio stream")
            logger.info(f"  Sample rate: {self.sample_rate} Hz")
            logger.info(f"  Channels: {self.n_channels}")
            logger.info(f"  Buffer size: {self.max_buffer_samples} samples")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Audio stream: {e}")
            return False

    def process_audio_chunk(self, samples: np.ndarray, timestamps: np.ndarray) -> Dict:
        """
        Process audio chunk and compute metrics

        Args:
            samples: Audio samples (n_samples, n_channels)
            timestamps: LSL timestamps

        Returns:
            Dict with audio data and metrics
        """
        # Add to rolling buffer
        self.audio_buffer.append(samples)
        self.timestamp_buffer.extend(timestamps)

        # Trim buffer to window size
        total_samples = sum(len(chunk) for chunk in self.audio_buffer)
        while total_samples > self.max_buffer_samples and len(self.audio_buffer) > 1:
            removed = self.audio_buffer.pop(0)
            self.timestamp_buffer = self.timestamp_buffer[len(removed):]
            total_samples -= len(removed)

        # Concatenate buffer
        if not self.audio_buffer:
            return None

        audio_data = np.vstack(self.audio_buffer) if len(self.audio_buffer) > 1 else self.audio_buffer[0]

        # Flatten if mono
        if self.n_channels == 1 and audio_data.ndim > 1:
            audio_data = audio_data.flatten()

        # Compute metrics
        rms = float(np.sqrt(np.mean(audio_data ** 2)))
        peak = float(np.max(np.abs(audio_data)))

        # Downsample for transmission (max 200 points)
        downsample_factor = max(1, len(audio_data) // 200)
        downsampled = audio_data[::downsample_factor]

        return {
            'timestamp': self.timestamp_buffer[-1] if self.timestamp_buffer else time.time(),
            'time_seconds': len(self.timestamp_buffer) / self.sample_rate if self.sample_rate else 0,
            'waveform': downsampled.tolist() if isinstance(downsampled, np.ndarray) else [downsampled],
            'sample_rate': self.sample_rate,
            'rms': rms,
            'peak': peak,
            'n_samples': len(audio_data)
        }

    def run(self, duration: Optional[float] = None, callback: Optional[Callable] = None):
        """
        Run audio monitoring loop

        Args:
            duration: Optional duration in seconds (None = infinite)
            callback: Optional callback function to receive audio updates
        """
        if not self.inlet:
            raise RuntimeError("Not connected to audio stream. Call connect_stream() first.")

        logger.info(f"Starting audio monitor (duration={duration or 'infinite'}s)")

        start_time = time.time()
        self.last_update_time = start_time

        try:
            while True:
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    logger.info("Audio monitor duration reached")
                    break

                # Pull audio chunk
                chunk, timestamps = self.inlet.pull_chunk(timeout=0.1)

                if chunk:
                    # Convert to numpy
                    samples = np.array(chunk)
                    timestamps = np.array(timestamps)

                    # Process chunk
                    current_time = time.time()
                    if (current_time - self.last_update_time) >= self.update_interval:
                        result = self.process_audio_chunk(samples, timestamps)

                        if result and callback:
                            callback(result)

                        self.last_update_time = current_time

                else:
                    # No data, small sleep
                    time.sleep(0.01)

        except KeyboardInterrupt:
            logger.info("Audio monitor interrupted")

        except Exception as e:
            logger.error(f"Audio monitor error: {e}")
            raise

        finally:
            logger.info("Audio monitor stopped")

    def close(self):
        """Close audio stream connection"""
        if self.inlet:
            self.inlet.close_stream()
            self.inlet = None
            logger.info("Audio stream closed")


# Test function
def test_audio_monitor():
    """Test audio monitor with live LSL stream"""
    logging.basicConfig(level=logging.INFO)

    monitor = AudioMonitor(window_seconds=2.0, update_interval=0.2)

    if not monitor.connect_stream(timeout=10.0):
        print("Failed to connect to audio stream")
        print("Make sure:")
        print("  1. Neurable Research Kit is running")
        print("  2. Audio LSL stream is active")
        print("  3. burst_recorder.py is running with --enable-audio")
        return

    def print_audio_update(result):
        print(f"Audio: RMS={result['rms']:.4f}, Peak={result['peak']:.4f}, "
              f"Samples={result['n_samples']}")

    try:
        monitor.run(duration=10.0, callback=print_audio_update)
    finally:
        monitor.close()


if __name__ == '__main__':
    test_audio_monitor()
