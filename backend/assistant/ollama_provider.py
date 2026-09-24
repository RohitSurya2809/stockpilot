"""
Ollama LLM Provider

Connects to Ollama API for local/remote LLM inference.
Reads configuration from environment variables (via config.py).
"""

import requests
from typing import Dict, Optional, List
from config import settings


class OllamaProvider:
    """
    Ollama API client for StockPilot assistant.

    Configuration is loaded from environment variables:
    - OLLAMA_BASE_URL: API endpoint
    - OLLAMA_MODEL: Model name
    - OLLAMA_THINK: Enable/disable thinking mode
    - OLLAMA_KEEP_ALIVE: Model persistence (-1 = keep loaded)
    """

    def __init__(self):
        """Initialize Ollama provider with configuration from settings."""
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.think = settings.ollama_think
        self.keep_alive = settings.ollama_keep_alive

        print(f"[Ollama Provider] Initialized:")
        print(f"  Base URL: {self.base_url}")
        print(f"  Model: {self.model}")
        print(f"  Think mode: {self.think}")
        print(f"  Keep alive: {self.keep_alive}")

    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text completion using Ollama.

        Args:
            prompt: User prompt
            context: Optional context to prepend
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            requests.RequestException: If Ollama API is unreachable
        """
        # Build full prompt
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": temperature
            }
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        # Make request to Ollama API
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60  # 60 second timeout
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except requests.exceptions.ConnectionError:
            raise Exception(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Ensure Ollama is running and accessible at that address."
            )
        except requests.exceptions.Timeout:
            raise Exception(
                f"Ollama request timed out. The model may be loading or the server is overloaded."
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API error: {str(e)}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate chat completion using Ollama chat API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
        }

        options = {}
        if temperature != 0.7:
            options["temperature"] = temperature
        if max_tokens:
            options["num_predict"] = max_tokens
        if options:
            payload["options"] = options

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()

            result = response.json()
            return result.get("message", {}).get("content", "")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama chat API error: {str(e)}")

    def test_connection(self) -> Dict:
        """
        Test connection to Ollama server and verify model availability.

        Returns:
            Dict with connection status and model info
        """
        try:
            # Check if server is reachable
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()

            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]

            # Check if configured model is available
            model_available = self.model in model_names

            return {
                "connected": True,
                "base_url": self.base_url,
                "available_models": model_names,
                "configured_model": self.model,
                "model_available": model_available,
                "keep_alive": self.keep_alive,
                "think_mode": self.think
            }

        except requests.exceptions.ConnectionError:
            return {
                "connected": False,
                "error": f"Cannot connect to Ollama at {self.base_url}",
                "configured_model": self.model
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "configured_model": self.model
            }


# Test script
if __name__ == "__main__":
    print("="*70)
    print("OLLAMA PROVIDER - CONNECTION TEST")
    print("="*70)

    provider = OllamaProvider()

    print("\nTesting connection...")
    result = provider.test_connection()

    print("\nConnection Test Results:")
    print("-" * 70)
    for key, value in result.items():
        print(f"  {key}: {value}")

    if result.get("connected"):
        print("\n[OK] Ollama is accessible!")

        if result.get("model_available"):
            print(f"[OK] Model '{result['configured_model']}' is available!")

            # Test simple generation
            print("\nTesting simple generation...")
            try:
                response = provider.generate(
                    prompt="What is 2+2? Answer in one word.",
                    temperature=0.1
                )
                print(f"Response: {response[:200]}")
                print("\n[OK] Generation test successful!")
            except Exception as e:
                print(f"[ERROR] Generation test failed: {e}")
        else:
            print(f"[WARNING] Model '{result['configured_model']}' is NOT available")
            print(f"Available models: {result.get('available_models', [])}")
    else:
        print(f"\n[ERROR] Cannot connect to Ollama")
        print(f"Error: {result.get('error')}")

    print("\n" + "="*70)
