"""
Test Suite for Agent 26: Belief Tracker UI
Tests all API endpoints, UI functionality, and therapist workflows

Version: 1.0
Last Updated: 2025-11-18
"""

import pytest
import json
import asyncio
from pathlib import Path
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.belief_storage import BeliefStorage, BeliefQuery, BeliefClusterer
from src.belief_detector import BeliefDetector, Belief
from server.session_server import SessionServer


class TestBeliefAPIEndpoints(AioHTTPTestCase):
    """Test all belief API endpoints"""

    async def get_application(self):
        """Create test application"""
        server = SessionServer(host='localhost', port=8765, data_dir='test_data')
        return server.app

    async def setUpAsync(self):
        """Set up test database with sample beliefs"""
        await super().setUpAsync()

        # Create test beliefs database
        self.storage = BeliefStorage(db_path='test_data/beliefs_test.db')

        # Clear existing data
        # Clear existing data
        import sqlite3
        import unittest.mock
        
        # Patch BeliefStorage to use test database when instantiated in SessionServer
        self.storage_patcher = unittest.mock.patch('src.belief_storage.BeliefStorage')
        self.mock_storage_cls = self.storage_patcher.start()
        # Use the locally imported BeliefStorage class (which is the real one)
        self.mock_storage_cls.side_effect = lambda db_path=None: BeliefStorage(db_path='test_data/beliefs_test.db')
        
        with sqlite3.connect(self.storage.db_path) as conn:
            conn.execute('DELETE FROM beliefs')
            conn.execute('DELETE FROM belief_history')
            conn.commit()

        # Create sample beliefs
        self.sample_beliefs = [
            {
                'text': "I'm not good enough",
                'belief_type': 'self_worth',
                'confidence': 0.85,
                'evidence': "I feel like I'm not good enough for this job",
                'detected_at': '2025-11-18T14:00:00Z'
            },
            {
                'text': "I can't handle stress",
                'belief_type': 'capability',
                'confidence': 0.78,
                'evidence': "I just can't handle all this stress",
                'detected_at': '2025-11-18T14:15:00Z'
            },
            {
                'text': "The world is dangerous",
                'belief_type': 'safety',
                'confidence': 0.92,
                'evidence': "The world is so dangerous these days",
                'detected_at': '2025-11-18T14:30:00Z'
            },
            {
                'text': "I have no control",
                'belief_type': 'control',
                'confidence': 0.80,
                'evidence': "I have no control over my life",
                'detected_at': '2025-11-18T14:45:00Z'
            },
            {
                'text': "Nobody cares about me",
                'belief_type': 'relationships',
                'confidence': 0.75,
                'evidence': "Nobody really cares about me",
                'detected_at': '2025-11-18T15:00:00Z'
            }
        ]

        self.belief_ids = []
        for belief in self.sample_beliefs:
            belief_id = self.storage.create_belief('20251118_140000', belief)
            self.belief_ids.append(belief_id)

    async def tearDownAsync(self):
        """Clean up test database"""
        if hasattr(self, 'storage_patcher'):
            self.storage_patcher.stop()
        await super().tearDownAsync()

        # Remove test database
        db_path = Path('test_data/beliefs_test.db')
        if db_path.exists():
            db_path.unlink()

    @unittest_run_loop
    async def test_01_get_all_beliefs(self):
        """Test GET /api/beliefs - Get all beliefs"""
        resp = await self.client.request('GET', '/api/beliefs')
        assert resp.status == 200

        data = await resp.json()
        assert 'beliefs' in data
        assert 'count' in data
        assert data['count'] >= 5

    @unittest_run_loop
    async def test_02_get_beliefs_with_type_filter(self):
        """Test GET /api/beliefs?type=self_worth - Filter by type"""
        resp = await self.client.request('GET', '/api/beliefs?type=self_worth')
        assert resp.status == 200

        data = await resp.json()
        assert data['count'] >= 1

        # All beliefs should be self_worth type
        for belief in data['beliefs']:
            assert belief['belief_type'] == 'self_worth'

    @unittest_run_loop
    async def test_03_get_beliefs_with_confidence_filter(self):
        """Test GET /api/beliefs?min_confidence=0.8 - Filter by confidence"""
        resp = await self.client.request('GET', '/api/beliefs?min_confidence=0.8')
        assert resp.status == 200

        data = await resp.json()

        # All beliefs should have confidence >= 0.8
        for belief in data['beliefs']:
            assert belief['confidence'] >= 0.8

    @unittest_run_loop
    async def test_04_get_beliefs_with_status_filter(self):
        """Test GET /api/beliefs?status=active - Filter by status"""
        resp = await self.client.request('GET', '/api/beliefs?status=active')
        assert resp.status == 200

        data = await resp.json()

        # All beliefs should be active
        for belief in data['beliefs']:
            assert belief['status'] == 'active'

    @unittest_run_loop
    async def test_05_get_beliefs_with_search(self):
        """Test GET /api/beliefs?search=stress - Search beliefs"""
        resp = await self.client.request('GET', '/api/beliefs?search=stress')
        assert resp.status == 200

        data = await resp.json()
        assert data['count'] >= 1

        # At least one belief should contain 'stress'
        found = False
        for belief in data['beliefs']:
            if 'stress' in belief['text'].lower() or 'stress' in belief['context'].lower():
                found = True
                break

        assert found

    @unittest_run_loop
    async def test_06_get_single_belief(self):
        """Test GET /api/belief/{id} - Get specific belief"""
        belief_id = self.belief_ids[0]

        resp = await self.client.request('GET', f'/api/belief/{belief_id}')
        assert resp.status == 200

        data = await resp.json()
        assert 'belief' in data
        assert data['belief']['belief_id'] == belief_id

    @unittest_run_loop
    async def test_07_get_nonexistent_belief(self):
        """Test GET /api/belief/{id} - 404 for nonexistent belief"""
        resp = await self.client.request('GET', '/api/belief/nonexistent-id')
        assert resp.status == 404

        data = await resp.json()
        assert 'error' in data

    @unittest_run_loop
    async def test_08_validate_belief_success(self):
        """Test POST /api/belief/{id}/validate - Validate belief"""
        belief_id = self.belief_ids[0]

        payload = {
            'valid': True,
            'notes': 'Client shows pattern from childhood'
        }

        resp = await self.client.request(
            'POST',
            f'/api/belief/{belief_id}/validate',
            json=payload
        )

        assert resp.status == 200

        data = await resp.json()
        assert data['success'] is True
        assert data['validated'] is True

        # Verify belief was updated
        belief = self.storage.get_belief(belief_id)
        assert belief['validated'] is True
        assert belief['therapist_notes'] == 'Client shows pattern from childhood'

    @unittest_run_loop
    async def test_09_reject_belief(self):
        """Test POST /api/belief/{id}/validate - Reject belief"""
        belief_id = self.belief_ids[1]

        payload = {
            'valid': False,
            'notes': 'False positive detection'
        }

        resp = await self.client.request(
            'POST',
            f'/api/belief/{belief_id}/validate',
            json=payload
        )

        assert resp.status == 200

        data = await resp.json()
        assert data['success'] is True
        assert data['validated'] is False

    @unittest_run_loop
    async def test_10_update_belief_status(self):
        """Test PATCH /api/belief/{id}/status - Update status"""
        belief_id = self.belief_ids[2]

        payload = {
            'status': 'resolved',
            'therapist_notes': 'Addressed in session 5'
        }

        resp = await self.client.request(
            'PATCH',
            f'/api/belief/{belief_id}/status',
            json=payload
        )

        assert resp.status == 200

        data = await resp.json()
        assert data['success'] is True
        assert data['status'] == 'resolved'

        # Verify belief was updated
        belief = self.storage.get_belief(belief_id)
        assert belief['status'] == 'resolved'
        assert 'Addressed in session 5' in belief['therapist_notes']

    @unittest_run_loop
    async def test_11_update_belief_status_missing_status(self):
        """Test PATCH /api/belief/{id}/status - Missing status returns 400"""
        belief_id = self.belief_ids[0]

        payload = {
            'therapist_notes': 'Some notes'
        }

        resp = await self.client.request(
            'PATCH',
            f'/api/belief/{belief_id}/status',
            json=payload
        )

        assert resp.status == 400

        data = await resp.json()
        assert 'error' in data

    @unittest_run_loop
    async def test_12_get_belief_clusters(self):
        """Test GET /api/beliefs/clusters - Get clustered beliefs"""
        # Add similar beliefs for clustering
        similar_beliefs = [
            {
                'text': "I'm not smart enough",
                'belief_type': 'self_worth',
                'confidence': 0.82,
                'evidence': "I'm not smart enough for this",
                'detected_at': '2025-11-18T16:00:00Z'
            },
            {
                'text': "I'm not capable enough",
                'belief_type': 'self_worth',
                'confidence': 0.79,
                'evidence': "I'm just not capable enough",
                'detected_at': '2025-11-18T16:15:00Z'
            }
        ]

        for belief in similar_beliefs:
            self.storage.create_belief('20251118_160000', belief)

        resp = await self.client.request('GET', '/api/beliefs/clusters')
        assert resp.status == 200

        data = await resp.json()
        assert 'clusters' in data
        assert 'count' in data

    @unittest_run_loop
    async def test_13_get_belief_clusters_with_type_filter(self):
        """Test GET /api/beliefs/clusters?type=self_worth - Filter clusters"""
        resp = await self.client.request('GET', '/api/beliefs/clusters?type=self_worth')
        assert resp.status == 200

        data = await resp.json()
        assert 'clusters' in data

        # All clusters should be self_worth type
        for cluster in data['clusters']:
            assert cluster['belief_type'] == 'self_worth'

    @unittest_run_loop
    async def test_14_get_belief_trends(self):
        """Test GET /api/beliefs/trends - Get temporal trends"""
        resp = await self.client.request('GET', '/api/beliefs/trends?days=7')
        assert resp.status == 200

        data = await resp.json()
        assert 'trends' in data
        assert 'belief_type' in data
        assert 'days' in data
        assert data['days'] == 7

    @unittest_run_loop
    async def test_15_get_belief_trends_with_type(self):
        """Test GET /api/beliefs/trends?type=self_worth - Filter trends by type"""
        resp = await self.client.request('GET', '/api/beliefs/trends?type=self_worth&days=30')
        assert resp.status == 200

        data = await resp.json()
        assert data['belief_type'] == 'self_worth'
        assert data['days'] == 30

    @unittest_run_loop
    async def test_16_export_beliefs_json(self):
        """Test GET /api/beliefs/export?format=json - Export as JSON"""
        resp = await self.client.request('GET', '/api/beliefs/export?format=json')
        assert resp.status == 200

        data = await resp.json()
        assert 'exported_at' in data
        assert 'belief_count' in data
        assert 'beliefs' in data
        assert len(data['beliefs']) >= 5

    @unittest_run_loop
    async def test_17_export_beliefs_csv(self):
        """Test GET /api/beliefs/export?format=csv - Export as CSV"""
        resp = await self.client.request('GET', '/api/beliefs/export?format=csv')
        assert resp.status == 200

        csv_text = await resp.text()
        assert 'belief_id' in csv_text
        assert 'belief_type' in csv_text
        assert 'confidence' in csv_text

        # Should have multiple rows
        lines = csv_text.strip().split('\n')
        assert len(lines) >= 6  # header + 5 beliefs

    @unittest_run_loop
    async def test_18_export_beliefs_with_filters(self):
        """Test GET /api/beliefs/export - Export with filters"""
        resp = await self.client.request('GET', '/api/beliefs/export?format=json&type=self_worth')
        assert resp.status == 200

        data = await resp.json()

        # All exported beliefs should be self_worth type
        for belief in data['beliefs']:
            assert belief['belief_type'] == 'self_worth'

    @unittest_run_loop
    async def test_19_get_belief_history(self):
        """Test GET /api/belief/{id}/history - Get change history"""
        belief_id = self.belief_ids[0]

        # Make some changes to create history
        self.storage.update_belief(belief_id, {'status': 'monitoring'})
        self.storage.validate_belief(belief_id, True, 'Validated after review')

        resp = await self.client.request('GET', f'/api/belief/{belief_id}/history')
        assert resp.status == 200

        data = await resp.json()
        assert 'history' in data
        assert 'count' in data
        assert data['count'] >= 2

        # History should include creation and changes
        history = data['history']
        change_types = [h['change_type'] for h in history]
        assert 'created' in change_types or 'status_changed' in change_types

    @unittest_run_loop
    async def test_20_get_belief_history_empty(self):
        """Test GET /api/belief/{id}/history - Empty history for new belief"""
        # Create new belief
        new_belief = {
            'text': "Test belief",
            'belief_type': 'future',
            'confidence': 0.70,
            'evidence': "Test evidence",
            'detected_at': '2025-11-18T17:00:00Z'
        }
        belief_id = self.storage.create_belief('20251118_170000', new_belief)

        resp = await self.client.request('GET', f'/api/belief/{belief_id}/history')
        assert resp.status == 200

        data = await resp.json()
        assert 'history' in data

        # Should have at least creation event
        assert data['count'] >= 1


class TestBeliefDetectorIntegration:
    """Test belief detector integration with storage"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BeliefDetector()
        self.storage = BeliefStorage(db_path='test_data/beliefs_integration_test.db')

    def teardown_method(self):
        """Clean up test database"""
        db_path = Path('test_data/beliefs_integration_test.db')
        if db_path.exists():
            db_path.unlink()

    def test_21_detect_and_store_beliefs(self):
        """Test detecting beliefs from transcript and storing them"""
        transcript = """
        I just feel like I'm not good enough for this job. Every time I try,
        I fail. I can't handle the stress and nobody cares about how I feel.
        The world is so dangerous and I have no control over anything.
        """

        # Detect beliefs
        beliefs = self.detector.detect_beliefs(transcript)

        assert len(beliefs) >= 3  # Should detect multiple beliefs

        # Store beliefs
        session_id = '20251118_140000'
        for belief in beliefs:
            belief_id = self.storage.create_belief(session_id, belief.to_dict())
            assert belief_id is not None

        # Verify storage
        stored_beliefs = self.storage.get_beliefs_by_session(session_id)
        assert len(stored_beliefs) >= 3

    def test_22_query_beliefs_by_type(self):
        """Test querying beliefs by type"""
        # Create test beliefs
        session_id = '20251118_150000'
        belief_types = ['self_worth', 'capability', 'safety', 'self_worth']

        for i, btype in enumerate(belief_types):
            belief_data = {
                'text': f'Test belief {i}',
                'belief_type': btype,
                'confidence': 0.8,
                'evidence': f'Test evidence {i}',
                'detected_at': '2025-11-18T15:00:00Z'
            }
            self.storage.create_belief(session_id, belief_data)

        # Query self_worth beliefs
        query = BeliefQuery(self.storage)
        results = query.query({'belief_types': ['self_worth']})

        assert len(results) >= 2  # Should find 2 self_worth beliefs

    def test_23_cluster_similar_beliefs(self):
        """Test clustering similar beliefs"""
        session_id = '20251118_160000'

        # Create similar beliefs
        similar_texts = [
            "I'm not good enough",
            "I'm not smart enough",
            "I'm not capable enough",
            "I can't do anything right"
        ]

        for text in similar_texts:
            belief_data = {
                'text': text,
                'belief_type': 'self_worth',
                'confidence': 0.8,
                'evidence': text,
                'detected_at': '2025-11-18T16:00:00Z'
            }
            self.storage.create_belief(session_id, belief_data)

        # Cluster beliefs
        clusterer = BeliefClusterer(self.storage, similarity_threshold=0.5)
        clusters = clusterer.cluster_beliefs('self_worth')

        # Should find at least 1 cluster
        assert len(clusters) >= 1

        # Cluster should have multiple members
        if clusters:
            assert clusters[0]['belief_count'] >= 2

    def test_24_therapist_validation_workflow(self):
        """Test complete therapist validation workflow"""
        # 1. Create belief
        session_id = '20251118_170000'
        belief_data = {
            'text': "I'm worthless",
            'belief_type': 'self_worth',
            'confidence': 0.90,
            'evidence': "I feel completely worthless",
            'detected_at': '2025-11-18T17:00:00Z'
        }
        belief_id = self.storage.create_belief(session_id, belief_data)

        # 2. Therapist validates belief
        success = self.storage.validate_belief(
            belief_id,
            is_valid=True,
            therapist_notes="Core belief identified, needs CBT intervention"
        )
        assert success

        # 3. Verify validation
        belief = self.storage.get_belief(belief_id)
        assert belief['validated'] is True
        assert 'CBT intervention' in belief['therapist_notes']

        # 4. Update status to monitoring
        success = self.storage.update_belief(belief_id, {'status': 'monitoring'})
        assert success

        # 5. Later mark as resolved
        success = self.storage.update_belief(belief_id, {'status': 'resolved'})
        assert success

        # 6. Check history
        history = self.storage.get_belief_history(belief_id)
        assert len(history) >= 3  # created, validated, status changes

    def test_25_temporal_trends_analysis(self):
        """Test temporal trends analysis"""
        session_id = '20251118_180000'

        # Create beliefs over time
        belief_data = {
            'belief_type': 'self_worth',
            'confidence': 0.8,
            'evidence': 'Test evidence',
        }

        for i in range(5):
            belief_data['text'] = f'Belief {i}'
            belief_data['detected_at'] = f'2025-11-{18+i}T18:00:00Z'
            self.storage.create_belief(session_id, belief_data)

        # Get trends
        query = BeliefQuery(self.storage)
        trends = query.get_temporal_trends('self_worth', days=30)

        assert 'trends' in trends
        assert len(trends['trends']) >= 1


# Run all tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
