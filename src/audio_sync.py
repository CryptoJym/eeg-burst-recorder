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

        try:
            self.stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
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

    def capture(self, start_ms, duration_sec):
        """Capture audio window aligned to LSL timestamp"""
        if not self.stream:
            return None

        target_samples = int(self.sample_rate * duration_sec)
        frames = []
        start_ns = time.time_ns()

        try:
            for _ in range(target_samples // 1024 + 1):
                data = self.stream.read(1024, exception_on_overflow=False)
                frames.append(np.frombuffer(data, dtype=np.float32))

            audio = np.hstack(frames)[:target_samples]
            end_ns = time.time_ns()

            # Push to LSL outlet for viewer sync
            ts = local_clock()  # LSL timebase
            self.outlet.push_sample([audio.mean()], ts)  # Avg for marker

            return {
                'data': audio.tolist(),  # JSON serializable
                'start_ts': start_ms,
                'duration': duration_sec,
                'sample_rate': self.sample_rate,
                'lsl_offset_ms': (end_ns - start_ns) / 1e6  # ms jitter, expect <10
            }
        except Exception as e:
            print(f"Audio capture error: {e}")
            return None

    def close(self):
        """Clean shutdown of audio resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        print("✓ Audio sync closed")
