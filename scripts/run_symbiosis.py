#!/usr/bin/env python3
"""
Symbiosis Pipeline Launcher

Runs EEG recording with transcription and heart polling enabled.
Computes consciousness tokens and exports timeline for Grok analysis.
"""

import sys
import os
import argparse
import yaml
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.timestamp_aligner import TimestampAligner
from src.transcriber import SymbiosisTranscriber
from src.heart_sync import HeartSyncer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Symbiosis Pipeline - EEG/Transcript/Heart Token Fusion"
    )
    parser.add_argument('--session', default='symbiosis_test', help='Session name')
    parser.add_argument('--mode', choices=['burst', 'continuous'], default='continuous')
    parser.add_argument('--enable-transcript', action='store_true', help='Enable transcription')
    parser.add_argument('--enable-heart', action='store_true', help='Enable heart monitoring')
    parser.add_argument('--config', default='config/symbiosis.yaml', help='Config file path')
    parser.add_argument('--duration', type=int, default=300, help='Session duration in seconds')

    args = parser.parse_args()

    # Load configuration
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        args.config
    )

    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return 1

    with open(config_path) as f:
        config = yaml.safe_load(f)

    logger.info(f"=== Symbiosis Pipeline v1.2 ===")
    logger.info(f"Session: {args.session}")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Transcription: {'enabled' if args.enable_transcript else 'disabled'}")
    logger.info(f"Heart monitoring: {'enabled' if args.enable_heart else 'disabled'}")

    # Initialize components
    aligner = TimestampAligner()

    transcriber = None
    if args.enable_transcript:
        try:
            transcriber = SymbiosisTranscriber(config, aligner)
        except ImportError as e:
            logger.error(f"Transcription initialization failed: {e}")
            logger.error("Install dependencies: pip install faster-whisper torch")
            return 1

    heart = None
    if args.enable_heart:
        heart = HeartSyncer(config)
        heart.start_polling()
        logger.info("✓ Heart polling started")

    # TODO: Integrate with burst_recorder or session_server
    # For now, provide usage instructions
    logger.info("\n=== Next Steps ===")
    logger.info("1. Start session_server.py with symbiosis mode")
    logger.info("2. Connect MW75 Neuro headphones")
    logger.info("3. Start recording session")
    logger.info("4. Transcripts and tokens will be computed in real-time")
    logger.info("5. Export via Grok modal in UI")

    logger.info("\n=== Components Ready ===")
    logger.info(f"✓ TimestampAligner: {aligner.base_ns}ns")
    if transcriber:
        logger.info(f"✓ Transcriber: {transcriber.get_stats()}")
    if heart:
        logger.info(f"✓ Heart: {heart.get_current_state()}")

    # Keep alive for demonstration
    try:
        input("\nPress Enter to stop...\n")
    except KeyboardInterrupt:
        pass

    if heart:
        heart.stop_polling()
    logger.info("✓ Symbiosis pipeline stopped")

    return 0


if __name__ == '__main__':
    sys.exit(main())
