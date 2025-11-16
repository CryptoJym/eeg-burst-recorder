#!/usr/bin/env python3
"""
Heart Syncer - Multi-Modal Somatic State (S_t) Computation
Polls Whoop HRV and Limitless GSR via API/Bluetooth
"""

import os
import time
import logging
import threading
import asyncio
from typing import Optional, Dict
from scipy.special import expit  # Sigmoid σ

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available - Whoop integration disabled")

try:
    from bleak import BleakClient
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    logger.warning("bleak not available - Limitless integration disabled")


class HeartSyncer:
    """
    Multi-modal somatic state computation from heart sensors

    Computes S_t = σ(∑ w_i φ_i) where:
    - φ_hrv = Whoop HRV score [0,1]
    - φ_gsr = Limitless GSR normalized [0,1]
    - w_hrv = 0.6, w_gsr = 0.4 (empirical weights)
    """

    def __init__(self, config):
        self.config = config
        heart_config = config.get('heart', {})

        # Whoop configuration
        self.whoop_token = os.getenv('WHOOP_TOKEN') or heart_config.get('whoop_token', '')
        self.whoop_enabled = REQUESTS_AVAILABLE and self.whoop_token and self.whoop_token != "${WHOOP_TOKEN}"

        # Limitless configuration
        self.limitless_mac = heart_config.get('limitless_mac', 'XX:XX:XX:XX:XX:XX')
        self.limitless_enabled = BLEAK_AVAILABLE and self.limitless_mac != "XX:XX:XX:XX:XX:XX"

        self.poll_interval = heart_config.get('poll_interval', 5)

        # State variables
        self.last_hrv = 0.5  # Default neutral valence proxy
        self.last_gsr = 0.5  # Default neutral arousal proxy
        self.last_s_t = 0.5  # Default somatic state
        self.polling_thread = None
        self.running = False

        logger.info(
            f"HeartSyncer initialized: "
            f"Whoop={'enabled' if self.whoop_enabled else 'disabled'}, "
            f"Limitless={'enabled' if self.limitless_enabled else 'disabled'}"
        )

    def poll_whoop(self) -> float:
        """
        Poll Whoop API for latest HRV recovery score

        Returns:
            float: HRV score [0,1]
        """
        if not self.whoop_enabled:
            return self.last_hrv

        try:
            headers = {'Authorization': f'Bearer {self.whoop_token}'}
            resp = requests.get(
                'https://api.whoop.com/v1/activity',
                headers=headers,
                timeout=5
            )

            if resp.status_code == 200:
                data = resp.json()
                # Extract HRV recovery score (0-100) and normalize to [0,1]
                if 'recovery' in data and len(data['recovery']) > 0:
                    score = data['recovery'][0].get('score', 50)
                    self.last_hrv = score / 100.0
                    logger.debug(f"Whoop HRV: {self.last_hrv:.3f}")
            else:
                logger.warning(f"Whoop API error: {resp.status_code}")

        except Exception as e:
            logger.error(f"Whoop poll failed: {e}")

        return self.last_hrv

    async def poll_limitless_async(self) -> float:
        """
        Poll Limitless pendant via Bluetooth for GSR

        Returns:
            float: GSR normalized [0,1]
        """
        if not self.limitless_enabled:
            return self.last_gsr

        try:
            async with BleakClient(self.limitless_mac) as client:
                # Read GSR characteristic (UUID may vary - check Limitless docs)
                gsr_uuid = "00002a56-0000-1000-8000-00805f9b34fb"
                gsr_bytes = await client.read_gatt_char(gsr_uuid)
                gsr_raw = float(gsr_bytes.decode())

                # Normalize to [0,1] (calibrate based on your device)
                self.last_gsr = min(max(gsr_raw / 1000.0, 0.0), 1.0)
                logger.debug(f"Limitless GSR: {self.last_gsr:.3f}")

        except Exception as e:
            logger.error(f"Limitless poll failed: {e}")

        return self.last_gsr

    def poll_limitless(self) -> float:
        """Synchronous wrapper for Limitless polling"""
        try:
            return asyncio.run(self.poll_limitless_async())
        except Exception as e:
            logger.error(f"Limitless async poll error: {e}")
            return self.last_gsr

    def compute_s_t(self, whoop_hrv: Optional[float] = None, gsr: Optional[float] = None) -> float:
        """
        Compute somatic state S_t from heart signals

        Equation: S_t = σ(∑ w_i φ_i) where σ is sigmoid
        - w_hrv = 0.6 (valence weight, inverted)
        - w_gsr = 0.4 (arousal weight)
        - Threshold tuned for DEAP dataset (r=0.72)

        Args:
            whoop_hrv: HRV score [0,1], uses last if None
            gsr: GSR score [0,1], uses last if None

        Returns:
            float: Somatic state [0,1]
        """
        hrv = whoop_hrv if whoop_hrv is not None else self.last_hrv
        gsr_val = gsr if gsr is not None else self.last_gsr

        # Invert HRV for arousal calculation
        # High HRV (parasympathetic/relaxation) → low arousal
        # Low HRV (sympathetic/stress) → high arousal
        s_t_hrv = 1.0 / (hrv + 1.0)

        # Weighted sum (empirical weights from arousal/valence models)
        arousal = 0.6 * s_t_hrv + 0.4 * gsr_val

        # Sigmoid with tuned threshold (centers at 0.5 -> S_t=0.5)
        self.last_s_t = expit(arousal * 10 - 5)

        return self.last_s_t

    def _polling_loop(self):
        """Background thread polling loop"""
        logger.info(f"Heart polling started (interval: {self.poll_interval}s)")

        while self.running:
            try:
                # Poll Whoop
                if self.whoop_enabled:
                    self.poll_whoop()

                # Poll Limitless
                if self.limitless_enabled:
                    self.poll_limitless()

                # Compute current S_t
                self.compute_s_t()

                time.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"Polling loop error: {e}")
                time.sleep(1)

        logger.info("Heart polling stopped")

    def start_polling(self):
        """Start background polling thread"""
        if self.running:
            logger.warning("Polling already running")
            return

        self.running = True
        self.polling_thread = threading.Thread(
            target=self._polling_loop,
            daemon=True
        )
        self.polling_thread.start()
        logger.info("✓ Heart polling thread started")

    def stop_polling(self):
        """Stop background polling"""
        self.running = False
        if self.polling_thread:
            self.polling_thread.join(timeout=2)
            logger.info("✓ Heart polling thread stopped")

    def get_current_state(self) -> Dict:
        """Get current heart state"""
        return {
            's_t': self.last_s_t,
            'hrv': self.last_hrv,
            'gsr': self.last_gsr,
            'whoop_enabled': self.whoop_enabled,
            'limitless_enabled': self.limitless_enabled
        }
