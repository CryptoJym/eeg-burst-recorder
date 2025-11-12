#!/usr/bin/env python3
"""
MindMeld EEG-Grok Pipeline Launcher

Simplified launcher for EEG burst recording with audio sync and Grok export.
Usage:
    python scripts/run_mindmeld.py --session grok_test_001
    python scripts/run_mindmeld.py --session talk_mode --mode continuous --duration 300
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from burst_recorder import EEGBurstRecorder


def main():
    parser = argparse.ArgumentParser(
        description="MindMeld EEG-Grok Pipeline for meditation and conversation analysis"
    )
    parser.add_argument(
        '--session',
        default='mindmeld_session',
        help="Session ID for tags/exports (default: mindmeld_session)"
    )
    parser.add_argument(
        '--config',
        default='config/meditation.yaml',
        help="YAML config file (default: config/meditation.yaml)"
    )
    parser.add_argument(
        '--mode',
        choices=['burst', 'continuous'],
        default='burst',
        help="Recording mode: burst for meditations, continuous for talks (default: burst)"
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=None,
        help="Recording duration in seconds (default: infinite)"
    )
    parser.add_argument(
        '--no-audio',
        action='store_true',
        help="Disable audio sync (default: enabled)"
    )

    args = parser.parse_args()

    # Build output directory from session
    output_dir = f"burst_data/{args.session}"

    print(f"\n{'='*60}")
    print("🧠 MindMeld EEG-Grok Pipeline")
    print(f"{'='*60}")
    print(f"Session: {args.session}")
    print(f"Mode: {args.mode}")
    print(f"Config: {args.config}")
    print(f"Audio: {'Disabled' if args.no_audio else 'Enabled'}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    # Create recorder with MindMeld features
    recorder = EEGBurstRecorder(
        config_file=args.config,
        enable_audio=not args.no_audio,
        mode=args.mode,
        output_dir=output_dir,
        send_markers=True
    )

    # Connect to LSL stream
    if not recorder.connect_to_stream(stream_type='EEG', timeout=10.0):
        print("\n❌ Failed to connect to LSL stream")
        print("Make sure Neurable Research Kit is running and streaming data")
        return 1

    # Run recording
    try:
        recorder.run(duration=args.duration)
    except KeyboardInterrupt:
        print("\n\n✓ MindMeld session ended")
    finally:
        # Cleanup audio sync
        if recorder.audio_sync:
            recorder.audio_sync.close()

    print(f"\n{'='*60}")
    print("📊 Session Complete")
    print(f"{'='*60}")
    print(f"Data saved to: {output_dir}/")
    print(f"Bursts/chunks: {recorder.burst_count}")

    if recorder.exporter:
        print(f"\n💡 To analyze with Grok:")
        print(f"   1. Decompress any .json.snappy file:")
        print(f"      python -c \"import snappy; print(snappy.uncompress(open('{output_dir}/burst_*.json.snappy','rb').read()).decode())\"")
        print(f"   2. Paste the JSON output to Grok for analysis")
        print(f"   3. Ask Grok: 'Analyze this EEG session for meditation patterns'")

    print(f"{'='*60}\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
