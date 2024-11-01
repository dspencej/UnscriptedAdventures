# llm/llm_config.py

import os
from typing import Dict, Any

def get_llm_config(provider: str) -> Dict[str, Any]:
    """
    Retrieves the LLM configuration based on the provider.

    :param provider: The LLM provider ('openai', 'ollama', etc.)
    :return: Configuration dictionary for the specified LLM provider
    """
    if provider == "ollama":
        config = {
            "config_list": [
                {
                    "model": "llama3:latest",  # Default model for Ollama
                    "base_url": "http://localhost:11434/v1",
                    "api_key": "ollama",
                    "price": [0, 0],
                }
            ],
            "timeout": 1000,
        }
        return config

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not set in environment variables.")

        config = {
            "config_list": [
                {
                    "model": "gpt-4",  # You can set this to a default model
                    "api_key": api_key,
                    "api_type": "openai",
                    "base_url": "https://api.openai.com/v1",
                    "n": 1,
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            ],
            "timeout": 1000,
        }
        return config

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
