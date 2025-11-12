#!/usr/bin/env python3
"""
Extract MindMeld burst data for Grok AI analysis
Usage: python extract_for_grok.py [session_name] [--burst burst_id | --all]
"""

import sys
import json
import snappy
from pathlib import Path
from datetime import datetime

def extract_single_burst(burst_file):
    """Extract and decompress a single burst"""
    with open(burst_file, 'rb') as f:
        compressed = f.read()

    decompressed = snappy.uncompress(compressed)
    data = json.loads(decompressed.decode('utf-8'))
    return data

def extract_session(session_dir):
    """Extract all bursts from a session"""
    bursts = []
    for snappy_file in sorted(session_dir.glob('burst_*.json.snappy')):
        burst = extract_single_burst(snappy_file)
        bursts.append(burst)

    return {
        'session_name': session_dir.name,
        'total_bursts': len(bursts),
        'first_burst_time': bursts[0]['timestamp'] if bursts else None,
        'last_burst_time': bursts[-1]['timestamp'] if bursts else None,
        'bursts': bursts
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_for_grok.py [session_name] [--burst burst_id | --all]")
        print("\nExamples:")
        print("  python extract_for_grok.py meditation_session_001 --all")
        print("  python extract_for_grok.py meditation_session_001 --burst burst_20251111_180753_0001")
        print("\nAvailable sessions:")
        burst_data_dir = Path('burst_data')
        if burst_data_dir.exists():
            for session in sorted(burst_data_dir.iterdir()):
                if session.is_dir():
                    num_bursts = len(list(session.glob('burst_*.json.snappy')))
                    print(f"  - {session.name} ({num_bursts} bursts)")
        sys.exit(1)

    session_name = sys.argv[1]
    session_dir = Path('burst_data') / session_name

    if not session_dir.exists():
        print(f"❌ Session not found: {session_name}")
        print(f"   Looking in: {session_dir.absolute()}")
        sys.exit(1)

    # Check for --burst or --all flag
    if len(sys.argv) > 2:
        if sys.argv[2] == '--all':
            print(f"📊 Extracting all bursts from session: {session_name}")
            data = extract_session(session_dir)
            print("\n" + "="*80)
            print("PASTE THE FOLLOWING TO GROK:")
            print("="*80 + "\n")
            print(json.dumps(data, indent=2))
            print("\n" + "="*80)
            print(f"✅ Extracted {data['total_bursts']} bursts")
            print("="*80)

        elif sys.argv[2] == '--burst':
            if len(sys.argv) < 4:
                print("❌ Please specify burst ID: --burst burst_20251111_180753_0001")
                sys.exit(1)

            burst_id = sys.argv[3]
            burst_file = session_dir / f"{burst_id}.json.snappy"

            if not burst_file.exists():
                print(f"❌ Burst not found: {burst_id}")
                print(f"   Looking in: {burst_file.absolute()}")
                sys.exit(1)

            print(f"📊 Extracting single burst: {burst_id}")
            data = extract_single_burst(burst_file)
            print("\n" + "="*80)
            print("PASTE THE FOLLOWING TO GROK:")
            print("="*80 + "\n")
            print(json.dumps(data, indent=2))
            print("\n" + "="*80)
            print(f"✅ Extracted burst {burst_id}")
            print("="*80)
    else:
        # Default: show session summary
        print(f"📊 Session: {session_name}")
        print(f"   Location: {session_dir.absolute()}")

        burst_files = list(session_dir.glob('burst_*.json.snappy'))
        print(f"   Bursts: {len(burst_files)}")

        if burst_files:
            print("\n📋 Available bursts:")
            for i, bf in enumerate(sorted(burst_files)[:10], 1):
                print(f"   {i}. {bf.stem}")

            if len(burst_files) > 10:
                print(f"   ... and {len(burst_files) - 10} more")

            print("\n💡 To extract:")
            print(f"   All bursts:      python extract_for_grok.py {session_name} --all")
            print(f"   Single burst:    python extract_for_grok.py {session_name} --burst {burst_files[0].stem}")

if __name__ == '__main__':
    main()
