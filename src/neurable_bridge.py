"""
Neurable MW75 Bridge

This module defines the specific channel mapping and functional roles for the Neurable MW75 headset.
It ensures that the generic LSL stream is correctly interpreted according to the Phase 4 Research Plan.

Channel Layout (12-14 channels typical):
- Frontal: Fp1, Fp2, F7, F8 (Executive function, decision making)
- Temporal: T7, T8, TP9, TP10 (Auditory processing, language)
- Parietal: P7, P8 (Integration, spatial mapping)
- Occipital: O1, O2 (Visual processing)
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger("NeurableBridge")

class NeurableMW75:
    """
    Defines the hardware specification and channel roles for Neurable MW75.
    """
    
    # Standard 10-20 Channel Names expected from MW75 LSL stream
    EXPECTED_CHANNELS = [
        "Fp1", "Fp2", "F7", "F8",  # Frontal
        "T7", "T8", "TP9", "TP10", # Temporal
        "P7", "P8",                # Parietal
        "O1", "O2"                 # Occipital
    ]
    
    # Functional roles for interpretation (Phase 4)
    CHANNEL_ROLES = {
        "Fp1": "Executive Function (Left) - Logic, Planning",
        "Fp2": "Executive Function (Right) - Emotion, Impulse Control",
        "F7": "Verbal Expression (Broca's Area proximity)",
        "F8": "Emotional Expression",
        "T7": "Auditory Processing (Left) - Language Comprehension",
        "T8": "Auditory Processing (Right) - Tone/Prosody",
        "TP9": "Auditory Integration (Left)",
        "TP10": "Auditory Integration (Right)",
        "P7": "Visuospatial Processing",
        "P8": "Integration",
        "O1": "Visual Processing (Left)",
        "O2": "Visual Processing (Right)"
    }
    
    @staticmethod
    def validate_stream(stream_channels: List[str]) -> bool:
        """
        Verify if the connected LSL stream matches the MW75 profile.
        """
        missing = [ch for ch in NeurableMW75.EXPECTED_CHANNELS if ch not in stream_channels]
        
        if missing:
            logger.warning(f"MW75 Validation Warning: Missing channels {missing}")
            # We return True if at least key channels are present to allow partial function
            critical = ["Fp1", "Fp2", "TP9", "TP10"]
            if any(c in missing for c in critical):
                logger.error("Critical MW75 channels missing!")
                return False
            return True
            
        logger.info("Neurable MW75 Stream Verified: All channels present.")
        return True

    @staticmethod
    def get_channel_role(channel_name: str) -> str:
        """Return the functional role of a channel."""
        return NeurableMW75.CHANNEL_ROLES.get(channel_name, "Unknown Region")
