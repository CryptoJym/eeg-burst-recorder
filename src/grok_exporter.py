"""
Grok JSON Exporter with Symbiosis Timeline Fusion

Compresses EEG/audio/metrics into snappy-compressed JSON for Grok analysis.
Symbiosis v1.2: Adds timeline array with word-level tokens and EEG/heart correlates.

Decompress with: python -c "import snappy; print(snappy.uncompress(open('file.json.snappy','rb').read()).decode())"
"""

import json
import time
import numpy as np
import snappy
from pathlib import Path
from .analyzer import quick_analyze, compute_token_for_word


class GrokExport:
    """Export burst data in Grok-friendly compressed JSON format"""

    @staticmethod
    def quick_analyze(eeg_samples, sample_rate, n_channels=14):
        """Delegate to analyzer module"""
        return quick_analyze(eeg_samples, sample_rate, n_channels)

    def dump(self, payload, path):
        """
        Save payload as snappy-compressed JSON.

        Args:
            payload: dict containing burst/chunk data
            path: output file path (e.g., 'session_001.json.snappy')
        """
        # Add export timestamp
        payload['export_ts'] = time.time()

        # Serialize to JSON
        json_str = json.dumps(payload, indent=2)

        # Compress with snappy
        compressed = snappy.compress(json_str.encode('utf-8'))

        # Write to file
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            f.write(compressed)

        # Also save uncompressed for debugging (optional)
        if payload.get('save_debug', False):
            debug_path = output_path.with_suffix('.debug.json')
            with open(debug_path, 'w') as f:
                f.write(json_str)

        print(f"✓ Exported {path} ({len(compressed)} bytes compressed)")
        print(f"  Decompress: python -c \"import snappy; print(snappy.uncompress(open('{path}','rb').read()).decode())\"")

    def load(self, path):
        """
        Load and decompress a Grok export file.

        Args:
            path: path to .json.snappy file

        Returns:
            dict: decompressed payload
        """
        with open(path, 'rb') as f:
            compressed = f.read()

        json_str = snappy.uncompress(compressed).decode('utf-8')
        return json.loads(json_str)

    def batch_export(self, session_dir, output_file='session_summary.json.snappy'):
        """
        Combine multiple burst exports into one session file.

        Args:
            session_dir: directory containing individual .json.snappy files
            output_file: name for combined output
        """
        session_path = Path(session_dir)
        burst_files = sorted(session_path.glob('burst_*.json.snappy'))

        if not burst_files:
            print(f"No burst files found in {session_dir}")
            return

        bursts = []
        for burst_file in burst_files:
            try:
                burst_data = self.load(burst_file)
                bursts.append(burst_data)
            except Exception as e:
                print(f"Warning: Could not load {burst_file}: {e}")

        # Create session summary
        summary = {
            'session_id': session_path.name,
            'num_bursts': len(bursts),
            'bursts': bursts,
            'created_at': time.time()
        }

        output_path = session_path / output_file
        self.dump(summary, str(output_path))

        print(f"\n✓ Combined {len(bursts)} bursts into {output_path}")
        print(f"  Paste decompressed JSON to Grok for analysis!")

    def dump_symbiosis_timeline(self, bursts, transcripts, heart_logs, session_id, eeg_data, config, path):
        """
        Create symbiosis timeline with word-level tokens fused to EEG/heart

        Args:
            bursts: List of burst dicts with EEG data
            transcripts: List of word dicts with timestamps
            heart_logs: List of heart state dicts with timestamps
            session_id: Session identifier
            eeg_data: Full session EEG array for windowing
            config: Configuration dict
            path: Output path for compressed JSON

        Returns:
            Timeline payload dict
        """
        timeline = []
        session_prior = eeg_data[:1000] if len(eeg_data) > 1000 else eeg_data  # First 1s as baseline

        # Match words to nearest heart states and compute tokens
        for word in transcripts:
            # Find nearest heart state (within 500ms)
            nearest_heart = None
            min_diff = float('inf')

            for h_log in heart_logs:
                diff = abs(h_log['timestamp_ms'] - word['start_ms'])
                if diff < min_diff and diff < 500:
                    min_diff = diff
                    nearest_heart = h_log

            s_t = nearest_heart['s_t'] if nearest_heart else 0.5

            # Compute token for this word
            token_data = compute_token_for_word(
                eeg_data, word, s_t, session_prior, config
            )

            if token_data:
                timeline.append(token_data)

        # Calculate predictions
        tokens = [t['token'] for t in timeline]
        avg_token = float(np.mean(tokens)) if tokens else 0.0
        flow_ratio = sum(1 for t in tokens if t > 0.4) / len(tokens) if tokens else 0.0

        payload = {
            'session': session_id,
            'timeline': timeline,
            'predictions': {
                'avg_token': avg_token,
                'flow_ratio': flow_ratio,
                'insight_count': sum(1 for t in tokens if t > 0.7),
                'word_count': len(timeline)
            },
            'metadata': {
                'duration_sec': eeg_data.shape[0] / 256 if len(eeg_data) > 0 else 0,
                'burst_count': len(bursts),
                'transcript_words': len(transcripts),
                'heart_samples': len(heart_logs)
            }
        }

        self.dump(payload, path)
        return payload
