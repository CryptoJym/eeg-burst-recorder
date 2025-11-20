"""
Agent 4: LLM Validator (Production Grade)

This module uses the Grok (xAI) LLM to provide meta-cognitive validation of the system.
It acts as a "Critic" agent, checking for:
1. Consistency: Do the EEG metrics match the user's spoken text?
2. Hallucinations: Are the system's claims supported by evidence?
3. Explainability: Translating raw bio-signals into human-readable insights.

Dependencies: openai (configured for xAI)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LLMValidator")

class LLMValidator:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM Validator with xAI configuration.
        
        Args:
            api_key: xAI API key. If None, reads from XAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No API key found. LLMValidator will fail on real calls.")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = "grok-3"

    def _query_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = True) -> Dict:
        """Helper to query the LLM with error handling."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1 if json_mode else 0.7,
                response_format={"type": "json_object"} if json_mode else None
            )
            content = response.choices[0].message.content
            if json_mode:
                return json.loads(content)
            return {"content": content}
        except Exception as e:
            logger.error(f"LLM Query Failed: {e}")
            return {"error": str(e)}

    def validate_token_consistency(self, token_data: Dict[str, float], text_transcript: str) -> Dict:
        """
        Check if the EEG state is consistent with the spoken text.
        
        Args:
            token_data: Dict of metrics (e.g., {'alpha': 0.8, 'theta': 0.2})
            text_transcript: The text spoken by the user at that moment.
            
        Returns:
            Dict with 'consistent' (bool) and 'reasoning' (str).
        """
        system_prompt = """
        You are a Neuro-Linguistic Validator. Your job is to check for consistency between a user's brain state (EEG metrics) and their spoken words.
        
        Rules:
        1. High Alpha (8-12Hz) -> Relaxed, idle, or internal focus.
        2. High Beta (13-30Hz) -> Active thinking, stress, or focus.
        3. High Theta (4-8Hz) -> Drowsiness, deep meditation, or memory retrieval.
        4. High Gamma (30Hz+) -> Insight, binding, or high cognitive load.
        
        Output JSON: {"consistent": bool, "reasoning": "string"}
        """
        
        user_prompt = f"""
        Analyze this pair:
        EEG Metrics: {json.dumps(token_data)}
        Spoken Text: "{text_transcript}"
        
        Is the brain state consistent with the text sentiment and complexity?
        """
        
        return self._query_llm(system_prompt, user_prompt)

    def detect_hallucination(self, claims: List[str], evidence: Dict[str, Any]) -> Dict:
        """
        Cross-reference system claims against raw data evidence to detect hallucinations.
        
        Args:
            claims: List of strings (e.g., ["User was stressed", "High cognitive load detected"])
            evidence: Raw data dict (e.g., {'heart_rate': 60, 'beta_power': 0.1})
            
        Returns:
            Dict with 'hallucinations' (List[str]) and 'verified_claims' (List[str]).
        """
        system_prompt = """
        You are a Fact-Checking Agent. Verify the following claims against the provided raw data evidence.
        If a claim is not supported by the data, label it as a hallucination.
        
        Output JSON: {"hallucinations": ["claim1"], "verified_claims": ["claim2"]}
        """
        
        user_prompt = f"""
        Claims: {json.dumps(claims)}
        Evidence: {json.dumps(evidence)}
        """
        
        return self._query_llm(system_prompt, user_prompt)

    def explain_brain_state(self, token_data: Dict[str, float]) -> str:
        """
        Translate raw metrics into a natural language explanation.
        
        Args:
            token_data: Dict of metrics.
            
        Returns:
            String explanation.
        """
        system_prompt = """
        You are a Neuro-Feedback Coach. Translate the following EEG metrics into a simple, encouraging 1-sentence explanation for the user.
        Avoid jargon. Focus on the mental state (relaxed, focused, flow, etc.).
        """
        
        user_prompt = f"Metrics: {json.dumps(token_data)}"
        
        result = self._query_llm(system_prompt, user_prompt, json_mode=False)
        return result.get("content", "Unable to generate explanation.")
