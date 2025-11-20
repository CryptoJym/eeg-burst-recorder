"""
Test Suite for Agent 4 (LLM Validator) - Production Grade

This test suite verifies the integration with the Grok (xAI) API.
It uses MOCKS to simulate API responses, ensuring that:
1. Prompts are constructed correctly.
2. JSON responses are parsed correctly.
3. Error handling works as expected.
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm_validator import LLMValidator

class TestLLMValidator(unittest.TestCase):
    
    def setUp(self):
        # Mock the OpenAI client to avoid real API calls
        self.patcher = patch('src.llm_validator.OpenAI')
        self.mock_openai = self.patcher.start()
        
        # Setup the mock client instance
        self.mock_client = MagicMock()
        self.mock_openai.return_value = self.mock_client
        
        self.validator = LLMValidator(api_key="fake-key")

    def tearDown(self):
        self.patcher.stop()

    def test_initialization(self):
        """Test that the client is initialized with the correct base_url for xAI."""
        self.mock_openai.assert_called_with(
            api_key="fake-key",
            base_url="https://api.x.ai/v1"
        )

    def test_validate_token_consistency_success(self):
        """Test successful consistency check."""
        # Mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "consistent": True,
            "reasoning": "Alpha aligns with relaxed text."
        })
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # Call method
        result = self.validator.validate_token_consistency(
            token_data={"alpha": 0.8},
            text_transcript="I feel so calm."
        )
        
        # Assertions
        self.assertTrue(result['consistent'])
        self.assertEqual(result['reasoning'], "Alpha aligns with relaxed text.")
        
        # Verify prompt content
        call_args = self.mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        self.assertIn("Neuro-Linguistic Validator", messages[0]['content'])
        self.assertIn("I feel so calm", messages[1]['content'])

    def test_detect_hallucination_success(self):
        """Test hallucination detection."""
        # Mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "hallucinations": ["User was stressed"],
            "verified_claims": []
        })
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # Call method
        result = self.validator.detect_hallucination(
            claims=["User was stressed"],
            evidence={"heart_rate": 60} # Low HR contradicts stress
        )
        
        # Assertions
        self.assertEqual(result['hallucinations'], ["User was stressed"])
        
        # Verify prompt
        call_args = self.mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        self.assertIn("Fact-Checking Agent", messages[0]['content'])

    def test_explain_brain_state_success(self):
        """Test natural language explanation."""
        # Mock response (non-JSON mode)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "You are in a state of deep flow."
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # Call method
        result = self.validator.explain_brain_state({"gamma": 0.9})
        
        # Assertions
        self.assertEqual(result, "You are in a state of deep flow.")
        
        # Verify json_mode was False
        call_args = self.mock_client.chat.completions.create.call_args
        self.assertIsNone(call_args.kwargs['response_format'])

    def test_api_error_handling(self):
        """Test graceful handling of API errors."""
        # Mock exception
        self.mock_client.chat.completions.create.side_effect = Exception("API Down")
        
        result = self.validator.validate_token_consistency({}, "")
        
        self.assertIn("error", result)
        self.assertEqual(result['error'], "API Down")

if __name__ == '__main__':
    unittest.main()
