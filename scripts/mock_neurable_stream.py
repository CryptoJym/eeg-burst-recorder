#!/usr/bin/env python3
"""
Mock Neurable MW75 Stream
-------------------------
Simulates the LSL output of a Neurable MW75 headset for testing.
Broadcasts 12 channels of EEG data at 250Hz.
"""

import time
import numpy as np
from pylsl import StreamInfo, StreamOutlet

def main():
    # Neurable MW75 Channel Layout (from neurable_bridge.py)
    channels = ["Fp1", "Fp2", "F7", "F8", "T7", "T8", "TP9", "TP10", "P7", "P8", "O1", "O2"]
    n_channels = len(channels)
    srate = 250
    
    print(f"Creating Mock MW75 Stream ({n_channels} channels @ {srate}Hz)...")
    
    info = StreamInfo('Neurable_MW75_Mock', 'EEG', n_channels, srate, 'float32', 'mock_mw75_id')
    
    # Add channel names to description
    chns = info.desc().append_child("channels")
    for label in channels:
        ch = chns.append_child("channel")
        ch.append_child_value("label", label)
        ch.append_child_value("unit", "microvolts")
        ch.append_child_value("type", "EEG")
        
    outlet = StreamOutlet(info)
    
    print(f"✓ Stream 'Neurable_MW75_Mock' started.")
    print("Press Ctrl+C to stop.")
    
    start_time = time.time()
    sent_samples = 0
    
    try:
        while True:
            # Generate random data (1 sample)
            # Add some sine waves to simulate alpha/theta
            elapsed = time.time() - start_time
            
            # Base noise
            sample = np.random.normal(0, 1, n_channels)
            
            # Add Alpha (10Hz) to Temporal/Parietal
            alpha = np.sin(2 * np.pi * 10 * elapsed) * 5
            sample[6:10] += alpha # TP9, TP10, P7, P8
            
            outlet.push_sample(sample)
            sent_samples += 1
            
            # Maintain rate
            time.sleep(1.0 / srate)
            
            if sent_samples % 250 == 0:
                print(f"\rSent {sent_samples} samples ({elapsed:.1f}s)", end='')
                
    except KeyboardInterrupt:
        print("\nStopping stream...")

if __name__ == "__main__":
    main()
