#!/usr/bin/env python3
"""
Example burst analysis script
Loads and visualizes EEG burst data
"""
import numpy as np
import json
import sys
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime


def load_burst(burst_path):
    """Load burst data from NPZ file"""
    burst_path = Path(burst_path)

    if not burst_path.exists():
        print(f"❌ File not found: {burst_path}")
        return None

    # Load NPZ
    data = np.load(burst_path)
    burst_info = {
        'data': data['data'],
        'sample_rate': float(data['sample_rate']),
        'channel_names': data['channel_names'].tolist(),
    }

    # Load JSON metadata if available
    meta_path = burst_path.with_name(burst_path.stem + '_meta.json')
    if meta_path.exists():
        with open(meta_path) as f:
            burst_info['metadata'] = json.load(f)

    return burst_info


def plot_burst(burst_info, save_path=None):
    """Create visualization of burst data"""
    data = burst_info['data']
    sample_rate = burst_info['sample_rate']
    channels = burst_info['channel_names']
    metadata = burst_info.get('metadata', {})

    n_samples, n_channels = data.shape
    time_axis = np.arange(n_samples) / sample_rate

    # Create figure
    fig, axes = plt.subplots(
        n_channels, 1,
        figsize=(14, 10),
        sharex=True
    )

    # Title
    burst_id = metadata.get('burst_id', 'Unknown')
    timestamp = metadata.get('timestamp', 'Unknown')
    fig.suptitle(f'EEG Burst: {burst_id}\n{timestamp}', fontsize=14, fontweight='bold')

    # Plot each channel
    for i, (ax, channel) in enumerate(zip(axes, channels)):
        # Remove DC offset
        channel_data = data[:, i] - np.mean(data[:, i])

        # Plot
        ax.plot(time_axis, channel_data, linewidth=0.8, color='#2E86AB')
        ax.set_ylabel(f'{channel}\n(µV)', fontsize=10, rotation=0, ha='right', va='center')
        ax.grid(True, alpha=0.3)

        # Mark trigger point
        pre_burst = metadata.get('pre_burst_seconds', 1.0)
        ax.axvline(pre_burst, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Trigger')

        # Add RMS/P2P annotations
        if 'channels' in metadata:
            triggered = [ch for ch in metadata['channels'] if ch['channel'] == channel]
            if triggered:
                info = triggered[0]
                rms = info.get('rms', 0)
                p2p = info.get('p2p', 0)
                ax.text(
                    0.02, 0.95,
                    f'RMS: {rms:.1f}µV  P2P: {p2p:.1f}µV',
                    transform=ax.transAxes,
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5),
                    fontsize=8,
                    va='top'
                )

    # X-axis label
    axes[-1].set_xlabel('Time (seconds)', fontsize=11)
    axes[-1].legend(loc='upper right')

    # Layout
    plt.tight_layout()

    # Save or show
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved to: {save_path}")
    else:
        plt.show()

    return fig


def analyze_burst(burst_info):
    """Print burst statistics"""
    data = burst_info['data']
    sample_rate = burst_info['sample_rate']
    channels = burst_info['channel_names']
    metadata = burst_info.get('metadata', {})

    print(f"\n{'='*60}")
    print("BURST ANALYSIS")
    print(f"{'='*60}\n")

    # Basic info
    print(f"Burst ID:     {metadata.get('burst_id', 'Unknown')}")
    print(f"Timestamp:    {metadata.get('timestamp', 'Unknown')}")
    print(f"Sample rate:  {sample_rate} Hz")
    print(f"Duration:     {data.shape[0] / sample_rate:.2f} seconds")
    print(f"Channels:     {data.shape[1]}")
    print(f"Total samples: {data.shape[0]}")

    # Thresholds
    if 'thresholds' in metadata:
        print(f"\nThresholds:")
        print(f"  RMS: {metadata['thresholds']['rms']} µV")
        print(f"  P2P: {metadata['thresholds']['p2p']} µV")

    # Triggered channels
    if 'channels' in metadata:
        print(f"\nTriggered Channels:")
        for ch_info in metadata['channels']:
            print(f"  {ch_info['channel']:6s}: RMS={ch_info['rms']:6.2f}µV  P2P={ch_info['p2p']:6.2f}µV")

    # Per-channel statistics
    print(f"\nAll Channel Statistics:")
    print(f"{'Channel':<10} {'Mean':>10} {'Std':>10} {'Min':>10} {'Max':>10} {'RMS':>10} {'P2P':>10}")
    print('-' * 70)

    for i, channel in enumerate(channels):
        channel_data = data[:, i]
        mean = np.mean(channel_data)
        std = np.std(channel_data)
        min_val = np.min(channel_data)
        max_val = np.max(channel_data)
        rms = np.sqrt(np.mean((channel_data - mean) ** 2))
        p2p = max_val - min_val

        print(f"{channel:<10} {mean:10.2f} {std:10.2f} {min_val:10.2f} {max_val:10.2f} {rms:10.2f} {p2p:10.2f}")

    print(f"\n{'='*60}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_burst.py <burst_file.npz> [--save <output.png>]")
        print("\nExample:")
        print("  python analyze_burst.py burst_data/burst_20251110_123456_0001.npz")
        print("  python analyze_burst.py burst_data/burst_20251110_123456_0001.npz --save plot.png")
        return 1

    burst_path = sys.argv[1]
    save_path = None

    # Check for --save flag
    if '--save' in sys.argv:
        save_idx = sys.argv.index('--save')
        if save_idx + 1 < len(sys.argv):
            save_path = sys.argv[save_idx + 1]

    # Load burst
    print(f"Loading burst from: {burst_path}")
    burst_info = load_burst(burst_path)

    if burst_info is None:
        return 1

    print(f"✓ Loaded {burst_info['data'].shape[0]} samples from {len(burst_info['channel_names'])} channels")

    # Analyze
    analyze_burst(burst_info)

    # Plot
    print("Creating visualization...")
    plot_burst(burst_info, save_path)

    return 0


if __name__ == '__main__':
    exit(main())
