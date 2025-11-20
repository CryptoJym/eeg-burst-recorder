"""
Test Suite for Agent 2 - NLP Analyzer (Production Grade)
Week 5 Implementation - Updated for Real Dependencies
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import src.nlp_analyzer as nlp_module
from src.nlp_analyzer import NLPAnalyzer

class TestNLPAnalyzer:
    
    def setup_method(self):
        """Setup mocks for optional dependencies before each test."""
        # 1. Force flags to True so we test the 'Real' logic paths
        self.orig_openai_avail = nlp_module.OPENAI_AVAILABLE
        self.orig_transformers_avail = nlp_module.TRANSFORMERS_AVAILABLE
        
        nlp_module.OPENAI_AVAILABLE = True
        nlp_module.TRANSFORMERS_AVAILABLE = True
        
        # 2. Inject Mock Classes (Always recreate to ensure test isolation)
        nlp_module.OpenAI = MagicMock()
        nlp_module.SentenceTransformer = MagicMock()
        
        nlp_module.util = MagicMock()
        # Mock cos_sim to return a tensor-like object with .item()
        nlp_module.util.cos_sim.return_value = MagicMock()
        nlp_module.util.cos_sim.return_value.item.return_value = 0.95
            
    def teardown_method(self):
        """Restore original state."""
        nlp_module.OPENAI_AVAILABLE = self.orig_openai_avail
        nlp_module.TRANSFORMERS_AVAILABLE = self.orig_transformers_avail
        
        # Optional: Clean up injected attributes if you want to be perfectly clean
        # but for this test suite it's fine.

    def test_initialization_defaults(self):
        """Test initialization."""
        analyzer = NLPAnalyzer()
        assert analyzer.concreteness_db["apple"] == 5.0

    def test_surprisal_computation_mocked(self):
        """Test surprisal calculation with mocked OpenAI."""
        # Setup the mock client that NLPAnalyzer will instantiate
        mock_client_cls = nlp_module.OpenAI
        mock_instance = mock_client_cls.return_value
        mock_response = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_response
        
        # Initialize analyzer (will use our injected Mock class)
        analyzer = NLPAnalyzer(openai_api_key="fake-key")
        
        text = "The quick brown fox"
        surprisals = analyzer.compute_surprisal(text)
        
        # Verify call was made
        mock_instance.chat.completions.create.assert_called_once()
        
        # Verify xAI base_url was used
        mock_client_cls.assert_called_with(
            api_key="fake-key",
            base_url="https://api.x.ai/v1"
        )
        
        # Since we didn't populate the complex response structure, it might return []
        # or the fallback. We just want to ensure it TRIED to use the API.
        assert isinstance(surprisals, list)

    def test_coherence_computation_mocked(self):
        """Test coherence calculation with mocked SentenceTransformer."""
        mock_model_cls = nlp_module.SentenceTransformer
        mock_instance = mock_model_cls.return_value
        
        # Mock encode to return tensors
        import torch
        # Create dummy embeddings: 3 sentences -> 3 vectors of size 2
        mock_instance.encode.return_value = torch.tensor([
            [1.0, 0.0], 
            [1.0, 0.0], 
            [0.0, 1.0]
        ])
        
        # Mock util.cos_sim to return different values for the two calls
        # Call 1: A->A (1.0), Call 2: A->B (0.0)
        mock_tensor_1 = MagicMock()
        mock_tensor_1.item.return_value = 0.99
        mock_tensor_2 = MagicMock()
        mock_tensor_2.item.return_value = 0.01
        
        nlp_module.util.cos_sim.side_effect = [mock_tensor_1, mock_tensor_2]
        
        analyzer = NLPAnalyzer(embedding_model_name="fake-model")
        
        sentences = ["A", "A", "B"]
        scores = analyzer.compute_coherence(sentences)
        
        # A->A (0.99), A->B (0.01)
        assert len(scores) == 2
        assert scores[0] > 0.9 
        assert scores[1] < 0.1
        
    def test_concreteness_lookup(self):
        """Test concreteness database lookup."""
        analyzer = NLPAnalyzer()
        assert analyzer.get_concreteness("apple") == 5.0
        
    def test_full_session_analysis(self):
        """Test aggregate analysis."""
        # Ensure mocks are ready for the full analysis
        mock_client_cls = nlp_module.OpenAI
        mock_instance = mock_client_cls.return_value
        mock_instance.chat.completions.create.return_value = MagicMock()
        
        analyzer = NLPAnalyzer(openai_api_key="fake")
        transcript = [
            {"text": "I have an idea", "timestamp": 1000},
            {"text": "It is about consciousness", "timestamp": 2000}
        ]
        
        metrics = analyzer.analyze_session_transcript(transcript)
        assert metrics["total_sentences"] > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
