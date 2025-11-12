"""
Audio-LSL Synchronization Module

Captures audio via PyAudio and syncs timestamps with LSL clock for
precise alignment with EEG burst events.
"""

import pyaudio
import numpy as np
import time
from pylsl import StreamInfo, StreamOutlet, local_clock


class AudioLSLSync:
    """Sync audio capture to LSL timebase for EEG correlation"""

    def __init__(self, config):
        self.sample_rate = config.get('sample_rate', 44100)
        self.stream_name = config.get('lsl_stream_name', 'Audio')
        self.p = pyaudio.PyAudio()
        self.is_streaming = False
        self.stream_thread = None

        # Rolling buffer for burst capture (store last 10 seconds)
        self.buffer_seconds = 10
        self.buffer = np.array([], dtype=np.float32)
        self.buffer_max_samples = int(self.sample_rate * self.buffer_seconds)

        try:
            self.stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024,
                stream_callback=self._audio_callback
            )
        except Exception as e:
            print(f"Warning: Could not open audio input: {e}")
            print("Audio sync disabled - continuing with EEG only")
            self.stream = None
            return

        # Optional LSL outlet for viewer sync (syncs timestamps)
        info = StreamInfo(
            name=self.stream_name,
            type='Audio',
            channel_count=1,
            nominal_srate=self.sample_rate,
            channel_format='float32',
            source_id='mic'
        )
        self.outlet = StreamOutlet(info)
        print(f"✓ Audio LSL outlet created for {self.stream_name}")

        # Start continuous streaming
        self.start_streaming()

    def capture(self, start_ms, duration_sec):
        """Capture audio window from rolling buffer aligned to LSL timestamp"""
        if not self.stream:
            return None

        try:
            # Extract most recent duration_sec from buffer
            target_samples = int(self.sample_rate * duration_sec)

            if len(self.buffer) < target_samples:
                print(f"Warning: Buffer only has {len(self.buffer)}/{target_samples} samples")
                audio = self.buffer.copy()
            else:
                audio = self.buffer[-target_samples:].copy()

            ts = local_clock()  # LSL timebase

            return {
                'data': audio.tolist(),  # JSON serializable
                'start_ts': start_ms,
                'duration': duration_sec,
                'sample_rate': self.sample_rate,
                'samples': len(audio),
                'lsl_timestamp': ts
            }
        except Exception as e:
            print(f"Audio capture error: {e}")
            return None

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback - pushes audio to LSL outlet in real-time"""
        if not self.is_streaming:
            return (in_data, pyaudio.paContinue)

        # Convert bytes to float32 numpy array
        audio_chunk = np.frombuffer(in_data, dtype=np.float32)

        # Add to rolling buffer for burst capture
        self.buffer = np.append(self.buffer, audio_chunk)
        if len(self.buffer) > self.buffer_max_samples:
            self.buffer = self.buffer[-self.buffer_max_samples:]

        # Push chunk to LSL outlet with LSL timestamp
        # Note: push_chunk is more efficient than push_sample for bulk data
        ts = local_clock()
        for i, sample in enumerate(audio_chunk):
            # Each sample gets slight timestamp offset based on position in chunk
            sample_ts = ts + (i / self.sample_rate)
            self.outlet.push_sample([sample], sample_ts)

        return (in_data, pyaudio.paContinue)

    def start_streaming(self):
        """Start continuous audio streaming to LSL"""
        if not self.stream:
            return False

        self.is_streaming = True
        self.stream.start_stream()
        print(f"✓ Audio streaming started ({self.sample_rate} Hz)")
        return True

    def stop_streaming(self):
        """Stop continuous audio streaming"""
        self.is_streaming = False
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
        print("✓ Audio streaming stopped")

    def close(self):
        """Clean shutdown of audio resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        print("✓ Audio sync closed")
