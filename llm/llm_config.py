# llm/llm_config.py
import os

# Select LLM provider: 'ollama' or 'openai'
LLM_PROVIDER = "openai"

# Common LLM configuration
OLLAMA_MODEL = "llama3:latest"
OLLAMA_BASE_URL = "http://localhost:11434/v1"  # Default Ollama API endpoint
OLLAMA_API_KEY = "ollama"

OPENAI_MODEL_3_5 = "gpt-3.5-turbo"
OPENAI_MODEL_4 = "gpt-4"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Store API key once

if LLM_PROVIDER == "ollama":
    CONFIG_LIST = [
        {
            "model": OLLAMA_MODEL,
            "base_url": OLLAMA_BASE_URL,
            "api_key": OLLAMA_API_KEY,
            "price": [0, 0],
        }
    ]
    llm_config = {
        "config_list": CONFIG_LIST,
        "timeout": 1000,
    }
    llm_config_DM = None
    llm_config_ST = None

elif LLM_PROVIDER == "openai":
    # Configuration for GPT-3.5
    CONFIG_LIST_3_5 = [
        {
            "model": OPENAI_MODEL_3_5,
            "api_key": OPENAI_API_KEY,
            "api_type": "openai",
            "base_url": "https://api.openai.com/v1",
            "n": 1,
            "max_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    ]

    # Configuration for GPT-4
    CONFIG_LIST_4 = [
        {
            "model": OPENAI_MODEL_4,
            "api_key": OPENAI_API_KEY,
            "api_type": "openai",
            "base_url": "https://api.openai.com/v1",
            "n": 1,
            "max_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    ]

    # Assign configurations
    llm_config_ST = {
        "config_list": CONFIG_LIST_3_5,
        "timeout": 1000,
    }
    llm_config_DM = {
        "config_list": CONFIG_LIST_4,
        "timeout": 1000,
    }
    llm_config = None

else:
    raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")
