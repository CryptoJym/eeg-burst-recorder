#!/usr/bin/env python3
"""
Symbiosis Transcriber - Faster-Whisper with Word-Level Timestamps
Provides real-time transcription synchronized to EEG timeline
"""

import numpy as np
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Faster-Whisper not available - transcription disabled")

from src.timestamp_aligner import TimestampAligner


class SymbiosisTranscriber:
    """Word-level transcription with nanosecond timestamp precision"""

    def __init__(self, config, aligner: Optional[TimestampAligner] = None):
        if not WHISPER_AVAILABLE:
            raise ImportError("faster-whisper and torch required for transcription")

        self.config = config
        self.aligner = aligner or TimestampAligner()

        # Initialize Whisper model with MPS support for Mac
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        compute_type = "int8" if device == "cpu" else "float16"

        model_size = config.get('transcriber', {}).get('model', 'base')
        logger.info(f"Initializing Whisper model '{model_size}' on {device}")

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )

        self.language = config.get('transcriber', {}).get('language', 'en')
        self.total_words = 0
        logger.info(f"✓ Transcriber ready (language: {self.language})")

    def transcribe_chunk(
        self,
        audio_data: np.ndarray,
        chunk_start_ms: float,
        sample_rate: int = 44100
    ) -> List[Dict]:
        """
        Transcribe audio chunk with word-level timestamps

        Args:
            audio_data: Mono float32 audio samples
            chunk_start_ms: Timestamp when chunk started (from aligner)
            sample_rate: Audio sample rate in Hz

        Returns:
            List of word dictionaries with timestamps and confidence
        """
        # Ensure float32 format
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Normalize audio
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))

        # Transcribe with word timestamps
        segments, info = self.model.transcribe(
            audio_data,
            language=self.language,
            vad_filter=True,  # Voice activity detection
            word_timestamps=True,
            beam_size=5
        )

        timeline = []
        for segment in segments:
            if not hasattr(segment, 'words'):
                continue

            for word in segment.words:
                # Calculate absolute timestamps relative to session start
                word_start_ms = chunk_start_ms + (word.start * 1000)
                word_end_ms = chunk_start_ms + (word.end * 1000)

                word_entry = {
                    'text': word.word.strip(),
                    'start_ms': word_start_ms,
                    'end_ms': word_end_ms,
                    'duration_ms': word_end_ms - word_start_ms,
                    'confidence': word.probability
                }

                timeline.append(word_entry)
                self.total_words += 1

        # Filter low-confidence words
        filtered_timeline = [w for w in timeline if w['confidence'] > 0.8]

        logger.info(
            f"Transcribed {len(filtered_timeline)}/{len(timeline)} words "
            f"(chunk: {chunk_start_ms:.0f}ms, {len(audio_data)/sample_rate:.1f}s)"
        )

        return filtered_timeline

    def get_stats(self):
        """Get transcription statistics"""
        return {
            'total_words': self.total_words,
            'model': self.config.get('transcriber', {}).get('model', 'base'),
            'language': self.language
        }
