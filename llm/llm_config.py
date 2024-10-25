# llm/llm_config.py
import os

# Select LLM provider: 'ollama' or 'opal'
# LLM_PROVIDER = "ollama"
LLM_PROVIDER = "opal"

# Common LLM configuration
OLLAMA_MODEL = "mistral:v0.3"  # Replace with the desired model in Ollama
OLLAMA_BASE_URL = "http://localhost:11434/v1"  # Default Ollama API endpoint
OLLAMA_API_KEY = "ollama"

OPAL_MODEL = "meta-llama/Meta-Llama-3-70B-Instruct"
OPAL_API_URL = "https://opal.jhuapl.edu/v2/chat/completions"
OPAL_API_KEY = os.getenv("OPAL_CUI_TOKEN")

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
elif LLM_PROVIDER == "opal":
    CONFIG_LIST = [
        {
            "model": OPAL_MODEL,
            "model_client_cls": "CustomModelClient",
            "api_key": OPAL_API_KEY,
            "api_url": OPAL_API_URL,
            "is_cui": False,
            "accept_cui_tos": True,
            "n": 1,
            "max_tokens": 2048,
            "params": {
                "temperature": 1.0,
                "top_p": 1.0,
            },
        }
    ]
    llm_config = {
        "config_list": CONFIG_LIST,
        "timeout": 1000,
    }
else:
    raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")
