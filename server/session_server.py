#!/usr/bin/env python3
"""
EEG Session Server - Real-time WebSocket + REST API
Connects burst recorder and spectral analyzer to web UI
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import signal
import sys
import subprocess
import threading
from queue import Queue

from aiohttp import web
import aiohttp_cors

# Import our spectral analyzer and audio monitor
import sys
sys.path.insert(0, str(Path(__file__).parent))
from spectral_analyzer import SpectralAnalyzer
from audio_monitor import AudioMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SessionServer:
    """Main server managing sessions, WebSocket connections, and data flow"""

    def __init__(self, host='localhost', port=8765, data_dir='../burst_data'):
        self.host = host
        self.port = port
        # Convert to absolute path to avoid issues with relative paths
        self.data_dir = Path(data_dir).resolve()

        # WebSocket clients
        self.ws_clients: Set[web.WebSocketResponse] = set()

        # Current recording state
        self.current_session: Optional[Dict] = None
        self.session_start_time: Optional[datetime] = None

        # Background tasks
        self.burst_monitor_task: Optional[asyncio.Task] = None
        self.spectral_monitor_task: Optional[asyncio.Task] = None
        self.audio_monitor_task: Optional[asyncio.Task] = None

        # Real-time data processors
        self.burst_subprocess: Optional[subprocess.Popen] = None
        self.spectral_analyzer: Optional[SpectralAnalyzer] = None
        self.spectral_queue: Queue = Queue()
        self.audio_monitor: Optional[AudioMonitor] = None
        self.audio_queue: Queue = Queue()
        self.burst_timestamps: List[float] = []  # For artifact-aware spectral

        # App
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()

    def setup_routes(self):
        """Configure HTTP routes"""
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_post('/api/sessions/start', self.start_session)
        self.app.router.add_post('/api/sessions/stop', self.stop_session)
        self.app.router.add_get('/api/sessions/{session_id}', self.get_session)
        self.app.router.add_get('/api/sessions', self.list_sessions)
        self.app.router.add_get('/api/status', self.get_status)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/api/sessions/{session_id}/grok', self.export_for_grok)
        self.app.router.add_get('/api/sessions-list', self.list_sessions_with_bursts)

        # Serve static UI files
        ui_dir = Path(__file__).parent.parent / 'ui'
        self.app.router.add_static('/ui', ui_dir)

    def setup_cors(self):
        """Enable CORS for local development"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*"
            )
        })

        # Apply CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)

    async def websocket_handler(self, request):
        """Handle WebSocket connections from UI"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.ws_clients.add(ws)
        logger.info(f"WebSocket client connected. Total clients: {len(self.ws_clients)}")

        try:
            # Send current state immediately
            await self.send_to_client(ws, {
                'type': 'connection',
                'status': 'connected',
                'timestamp': datetime.now().isoformat()
            })

            if self.current_session:
                await self.send_to_client(ws, {
                    'type': 'session_status',
                    'session': self.current_session,
                    'recording': True
                })

            # Keep connection alive and handle messages
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self.handle_ws_message(ws, data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON from client: {msg.data}")
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
        finally:
            self.ws_clients.discard(ws)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.ws_clients)}")

        return ws

    async def handle_ws_message(self, ws: web.WebSocketResponse, data: dict):
        """Process messages from WebSocket clients"""
        msg_type = data.get('type')

        if msg_type == 'ping':
            await self.send_to_client(ws, {'type': 'pong'})
        elif msg_type == 'request_status':
            await self.send_status(ws)
        else:
            logger.warning(f"Unknown WebSocket message type: {msg_type}")

    async def send_to_client(self, ws: web.WebSocketResponse, data: dict):
        """Send data to a specific WebSocket client"""
        try:
            await ws.send_json(data)
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    async def broadcast(self, data: dict):
        """Broadcast data to all connected WebSocket clients"""
        if not self.ws_clients:
            return

        # Send to all clients concurrently
        await asyncio.gather(
            *[self.send_to_client(ws, data) for ws in self.ws_clients],
            return_exceptions=True
        )

    async def start_session(self, request):
        """Start a new recording session"""
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({'error': 'Invalid JSON'}, status=400)

        if self.current_session:
            return web.json_response(
                {'error': 'Session already in progress'},
                status=400
            )

        # Create session object
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_session = {
            'id': session_id,
            'name': data.get('name', f'Session {session_id}'),
            'tags': data.get('tags', []),
            'notes': data.get('notes', ''),
            'methods': data.get('methods', ['spectral', 'burst']),
            'duration': data.get('duration'),  # None = continuous
            'thresholds': {
                'rms': data.get('threshold_rms', 50.0),
                'p2p': data.get('threshold_p2p', 100.0)
            },
            'started_at': datetime.now().isoformat(),
            'burst_count': 0,
            'samples_processed': 0
        }

        self.session_start_time = datetime.now()

        logger.info(f"Starting session: {session_id}")

        # Create session directory immediately
        session_dir = self.data_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created session directory: {session_dir}")

        # Start monitoring tasks
        if 'burst' in self.current_session['methods']:
            self.burst_monitor_task = asyncio.create_task(
                self.monitor_burst_recorder()
            )

        if 'spectral' in self.current_session['methods']:
            self.spectral_monitor_task = asyncio.create_task(
                self.monitor_spectral_analyzer()
            )

        # Start audio monitoring if available
        self.audio_monitor_task = asyncio.create_task(
            self.monitor_audio_stream()
        )

        # Notify clients
        await self.broadcast({
            'type': 'session_started',
            'session': self.current_session
        })

        return web.json_response({
            'success': True,
            'session': self.current_session
        })

    async def stop_session(self, request):
        """Stop the current recording session"""
        if not self.current_session:
            return web.json_response(
                {'error': 'No session in progress'},
                status=400
            )

        logger.info(f"Stopping session: {self.current_session['id']}")

        # Stop monitoring tasks (gracefully handle any errors)
        if self.burst_monitor_task:
            self.burst_monitor_task.cancel()
            try:
                await self.burst_monitor_task
            except (asyncio.CancelledError, Exception) as e:
                logger.warning(f"Burst monitor cleanup: {e}")

        if self.spectral_monitor_task:
            self.spectral_monitor_task.cancel()
            try:
                await self.spectral_monitor_task
            except (asyncio.CancelledError, Exception) as e:
                logger.warning(f"Spectral monitor cleanup: {e}")

        if self.audio_monitor_task:
            self.audio_monitor_task.cancel()
            try:
                await self.audio_monitor_task
            except (asyncio.CancelledError, Exception) as e:
                logger.warning(f"Audio monitor cleanup: {e}")

        # Finalize session
        session_data = self.current_session.copy()
        session_data['stopped_at'] = datetime.now().isoformat()

        elapsed = (datetime.now() - self.session_start_time).total_seconds()
        session_data['duration_seconds'] = elapsed

        # Save session metadata
        await self.save_session(session_data)

        # Notify clients
        await self.broadcast({
            'type': 'session_stopped',
            'session': session_data
        })

        # Clear current session
        self.current_session = None
        self.session_start_time = None

        return web.json_response({
            'success': True,
            'session': session_data
        })

    async def get_session(self, request):
        """Get details of a specific session"""
        session_id = request.match_info['session_id']

        # TODO: Load from database
        return web.json_response({
            'error': 'Not implemented yet'
        }, status=501)

    async def list_sessions(self, request):
        """List all recorded sessions"""
        # TODO: Load from database
        return web.json_response({
            'sessions': []
        })

    async def get_status(self, request):
        """Get current server status"""
        status = {
            'recording': self.current_session is not None,
            'clients_connected': len(self.ws_clients),
            'timestamp': datetime.now().isoformat()
        }

        if self.current_session:
            elapsed = (datetime.now() - self.session_start_time).total_seconds()
            status['session'] = {
                **self.current_session,
                'elapsed_seconds': elapsed
            }

        return web.json_response(status)

    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({'status': 'healthy'})

    async def send_status(self, ws: web.WebSocketResponse):
        """Send current status to a client"""
        status = {
            'type': 'status',
            'recording': self.current_session is not None,
            'timestamp': datetime.now().isoformat()
        }

        if self.current_session:
            elapsed = (datetime.now() - self.session_start_time).total_seconds()
            status['session'] = {
                **self.current_session,
                'elapsed_seconds': elapsed
            }

        await self.send_to_client(ws, status)

    async def monitor_burst_recorder(self):
        """Monitor burst recorder output and broadcast events"""
        logger.info("Starting burst monitor with live data")

        # Start burst recorder subprocess
        burst_script = Path(__file__).parent.parent / "burst_recorder.py"

        cmd = [
            sys.executable,
            str(burst_script),
            "--threshold-rms", str(self.current_session['thresholds']['rms']),
            "--threshold-p2p", str(self.current_session['thresholds']['p2p']),
            "--output-dir", str(self.data_dir / self.current_session['id']),
            "--enable-audio"  # Always enable audio for MindMeld
        ]

        # Add duration if specified
        if self.current_session.get('duration'):
            cmd.extend(["--duration", str(self.current_session['duration'])])

        try:
            self.burst_subprocess = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            logger.info(f"Burst recorder started: PID {self.burst_subprocess.pid}")

            burst_count = 0

            # Monitor stdout for burst detections
            while True:
                line = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.burst_subprocess.stdout.readline
                )

                if not line:
                    # Process ended
                    break

                # Look for burst save confirmation line
                if "✓ Burst #" in line and "saved:" in line:
                    burst_count += 1

                    # Extract burst_id from line (e.g., "✓ Burst #1 saved: burst_20251111_162642_0001")
                    parts = line.split("saved:")
                    if len(parts) == 2:
                        burst_id = parts[1].strip()
                        timestamp = datetime.now()

                        # Track timestamp for artifact-aware spectral
                        elapsed = (timestamp - self.session_start_time).total_seconds()
                        self.burst_timestamps.append(elapsed)

                        # Try to read metadata file for channel info
                        channels = []
                        metrics = {}
                        try:
                            meta_file = self.data_dir / self.current_session['id'] / f"{burst_id}_meta.json"
                            if meta_file.exists():
                                with open(meta_file, 'r') as f:
                                    meta = json.load(f)
                                    channels = [ch['channel'] for ch in meta.get('channels', [])]
                                    # Get RMS values for metrics
                                    metrics = {ch['channel']: {'rms': ch['rms'], 'p2p': ch['p2p']}
                                              for ch in meta.get('channels', [])}
                        except Exception as e:
                            logger.warning(f"Could not read burst metadata: {e}")

                        burst_event = {
                            'type': 'burst_detected',
                            'burst_id': burst_id,
                            'timestamp': timestamp.isoformat(),
                            'time_seconds': elapsed,
                            'channels': channels,
                            'metrics': metrics
                        }

                        # Update session
                        if self.current_session:
                            self.current_session['burst_count'] = burst_count

                        # Broadcast to clients
                        await self.broadcast(burst_event)
                        logger.info(f"Broadcasted burst #{burst_count}: {burst_id}")

        except asyncio.CancelledError:
            logger.info("Burst monitor cancelled")
            if self.burst_subprocess:
                self.burst_subprocess.terminate()
                self.burst_subprocess.wait()
            raise

        except Exception as e:
            logger.error(f"Burst monitor error: {e}")
            raise

    async def monitor_spectral_analyzer(self):
        """Monitor spectral analyzer output and broadcast band powers"""
        logger.info("Starting spectral monitor with live data")

        try:
            # Create spectral analyzer instance
            output_file = self.data_dir / self.current_session['id'] / 'spectral_data.csv'
            self.spectral_analyzer = SpectralAnalyzer(
                window_seconds=2.0,
                overlap=0.5,
                output_interval=1.0,
                output_file=str(output_file),
                artifact_timestamps=self.burst_timestamps
            )

            # Connect to LSL stream (gracefully handle missing hardware)
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.spectral_analyzer.connect_stream
                )
            except RuntimeError as e:
                logger.warning(f"No EEG stream available - spectral analysis disabled: {e}")
                # Notify clients that spectral is unavailable
                await self.broadcast({
                    'type': 'spectral_unavailable',
                    'reason': 'No EEG hardware connected',
                    'message': 'Connect MW75 headphones and start Neurable Research Kit'
                })
                return

            # Setup output file
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.spectral_analyzer.setup_output_file,
                str(output_file)
            )

            logger.info("Spectral analyzer connected to stream")

            # Callback for spectral updates
            def spectral_callback(result):
                # Put result in queue for async processing
                self.spectral_queue.put(result)

            # Start spectral analysis in background thread
            analysis_thread = threading.Thread(
                target=self.spectral_analyzer.run,
                kwargs={
                    'duration': self.current_session.get('duration'),
                    'callback': spectral_callback
                },
                daemon=True
            )
            analysis_thread.start()

            # Process spectral updates from queue
            while True:
                # Check queue for new spectral data
                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.spectral_queue.get(timeout=0.1)
                    )

                    spectral_event = {
                        'type': 'spectral_update',
                        'timestamp': result['timestamp'],
                        'time_seconds': result['time_seconds'],
                        'bands': result['bands'],
                        'quality': result['quality'],
                        'is_artifact': result['is_artifact']
                    }

                    # Broadcast to clients
                    await self.broadcast(spectral_event)

                except Exception as e:
                    # No data in queue, keep waiting
                    # This catches queue.Empty when timeout expires
                    await asyncio.sleep(0.1)

                # Check if thread is still alive
                if not analysis_thread.is_alive():
                    logger.info("Spectral analysis thread ended")
                    break

        except asyncio.CancelledError:
            logger.info("Spectral monitor stopped")
            raise

        except Exception as e:
            logger.error(f"Spectral monitor error: {e}")
            raise

    async def monitor_audio_stream(self):
        """Monitor audio LSL stream and broadcast waveform data"""
        logger.info("Starting audio monitor")

        try:
            # Create audio monitor instance
            self.audio_monitor = AudioMonitor(
                window_seconds=1.0,
                update_interval=0.1  # 10Hz updates
            )

            # Try to connect to audio stream (non-blocking, may fail if no audio)
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.audio_monitor.connect_stream(timeout=2.0)
            )

            if not self.audio_monitor.inlet:
                logger.warning("No audio stream available - continuing without audio")
                return

            logger.info("Audio monitor connected to stream")

            # Callback for audio updates
            def audio_callback(result):
                # Put result in queue for async processing
                self.audio_queue.put(result)

            # Start audio monitoring in background thread
            audio_thread = threading.Thread(
                target=self.audio_monitor.run,
                kwargs={
                    'duration': self.current_session.get('duration'),
                    'callback': audio_callback
                },
                daemon=True
            )
            audio_thread.start()

            # Process audio updates from queue
            while True:
                # Check queue for new audio data
                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.audio_queue.get(timeout=0.1)
                    )

                    audio_event = {
                        'type': 'audio_update',
                        'timestamp': result['timestamp'],
                        'time_seconds': result['time_seconds'],
                        'waveform': result['waveform'],
                        'sample_rate': result['sample_rate'],
                        'rms': result['rms'],
                        'peak': result['peak']
                    }

                    # Broadcast to clients
                    await self.broadcast(audio_event)

                except Exception as e:
                    # No data in queue, keep waiting
                    await asyncio.sleep(0.1)

                # Check if thread is still alive
                if not audio_thread.is_alive():
                    logger.info("Audio monitor thread ended")
                    break

        except asyncio.CancelledError:
            logger.info("Audio monitor stopped")
            if self.audio_monitor:
                self.audio_monitor.close()
            raise

        except Exception as e:
            logger.error(f"Audio monitor error: {e}")
            # Don't raise - audio is optional
            return

    async def save_session(self, session_data: dict):
        """Save session metadata to file"""
        session_dir = self.data_dir / session_data['id']
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file = session_dir / 'session.json'
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        logger.info(f"Session saved to {session_file}")

    async def list_sessions_with_bursts(self, request):
        """List all sessions with burst counts"""
        try:
            sessions = []

            if self.data_dir.exists():
                for session_dir in sorted(self.data_dir.iterdir(), reverse=True):
                    if session_dir.is_dir():
                        # Count bursts
                        burst_files = list(session_dir.glob('burst_*.json.snappy'))

                        # Get session metadata if available
                        session_file = session_dir / 'session.json'
                        session_data = {}
                        if session_file.exists():
                            with open(session_file, 'r') as f:
                                session_data = json.load(f)

                        sessions.append({
                            'id': session_dir.name,
                            'burst_count': len(burst_files),
                            'name': session_data.get('name', session_dir.name),
                            'started_at': session_data.get('started_at'),
                            'duration_seconds': session_data.get('duration_seconds')
                        })

            return web.json_response({'sessions': sessions})

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def export_for_grok(self, request):
        """Export session bursts in Grok-ready JSON format"""
        session_id = request.match_info['session_id']
        session_dir = self.data_dir / session_id

        if not session_dir.exists():
            return web.json_response(
                {'error': f'Session not found: {session_id}'},
                status=404
            )

        try:
            import snappy

            bursts = []
            burst_files = sorted(session_dir.glob('burst_*.json.snappy'))

            if not burst_files:
                return web.json_response(
                    {'error': 'No bursts found in session'},
                    status=404
                )

            for burst_file in burst_files:
                try:
                    with open(burst_file, 'rb') as f:
                        compressed = f.read()
                    decompressed = snappy.uncompress(compressed)
                    burst_data = json.loads(decompressed.decode('utf-8'))
                    bursts.append(burst_data)
                except Exception as e:
                    logger.warning(f"Could not read burst {burst_file.name}: {e}")

            # Create Grok-ready export
            grok_export = {
                'session_name': session_id,
                'total_bursts': len(bursts),
                'first_burst_time': bursts[0].get('timestamp') if bursts else None,
                'last_burst_time': bursts[-1].get('timestamp') if bursts else None,
                'bursts': bursts
            }

            return web.json_response(grok_export)

        except ImportError:
            return web.json_response(
                {'error': 'snappy module not installed'},
                status=500
            )
        except Exception as e:
            logger.error(f"Error exporting for Grok: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def start(self):
        """Start the server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        logger.info(f"Server started at http://{self.host}:{self.port}")
        logger.info(f"WebSocket endpoint: ws://{self.host}:{self.port}/ws")

    async def cleanup(self):
        """Cleanup on shutdown"""
        logger.info("Shutting down server...")

        # Stop current session if running
        if self.current_session:
            logger.info("Stopping active session")
            # Stop monitoring tasks
            if self.burst_monitor_task:
                self.burst_monitor_task.cancel()
            if self.spectral_monitor_task:
                self.spectral_monitor_task.cancel()

        # Close all WebSocket connections
        for ws in list(self.ws_clients):
            await ws.close()

        logger.info("Server shutdown complete")


async def main():
    """Main entry point"""
    server = SessionServer()

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(server.cleanup())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await server.start()

    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await server.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
