# llm/agents.py

import logging
import os

import chromadb
from autogen import ConversableAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from chromadb.utils import embedding_functions

from llm.llm_config import LLM_PROVIDER, llm_config

# ============================
# Logging Configuration
# ============================

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add a console handler if not already present
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Custom Opal Model Client (Aligned with AutoGen ModelClient Protocol)
if LLM_PROVIDER == "opal":
    from types import SimpleNamespace

    import requests

    class CustomModelClient:
        def __init__(self, config, **kwargs):
            logger.debug("Configuring CustomModelClient")
            self.model_name = config["model"]
            self.api_key = config["api_key"]
            self.api_url = config.get(
                "api_url", "https://opal.jhuapl.edu/v2/chat/completions"
            )
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self.max_tokens = config.get("max_tokens", 2048)
            self.is_cui = config.get("is_cui", False)
            self.accept_cui_tos = config.get("accept_cui_tos", True)
            logger.debug(f"Initialized Opal Model Client for model {self.model_name}")

        def create(self, params):
            messages = params.get("messages")
            n = params.get("n", 1)
            stream = params.get("stream", False)
            temperature = params.get("temperature", 1.0)
            top_p = params.get("top_p", 1.0)
            max_tokens = params.get("max_tokens", self.max_tokens)

            payload = {
                "model": self.model_name,
                "messages": messages,
                "n": n,
                "stream": stream,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "is_cui": self.is_cui,
                "accept_cui_tos": self.accept_cui_tos,
            }

            response = SimpleNamespace()
            response.choices = []
            response.model = self.model_name

            try:
                # Make the API call and log the response
                resp = requests.post(
                    self.api_url, headers=self.headers, json=payload, verify=False
                )
                resp.raise_for_status()
                data = resp.json()

                for choice in data.get("choices", []):
                    message = choice.get("message", {})
                    choice_ns = SimpleNamespace()
                    choice_ns.message = SimpleNamespace(
                        content=message.get("content"),
                        role=message.get("role"),
                        function_call=message.get("function_call", None),
                    )
                    response.choices.append(choice_ns)

                response.usage = data.get("usage", {})
            except Exception as e:
                logger.debug(f"Exception during API call: {e}")
                raise e

            return response

        def message_retrieval(self, response):
            return [choice.message.content for choice in response.choices]

        def cost(self, response) -> float:
            response.cost = 0
            return 0

        @staticmethod
        def get_usage(response):
            return response.usage if hasattr(response, "usage") else {}


# Initialize ChromaDB clients for DM and Storyteller agents
CHROMA_DB_PATH_DM = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "chromadb_dm")
)
CHROMA_DB_PATH_ST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "chromadb_st")
)
chroma_client_dm = chromadb.PersistentClient(path=CHROMA_DB_PATH_DM)
chroma_client_st = chromadb.PersistentClient(path=CHROMA_DB_PATH_ST)

# Initialize embedding model for retrieval
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)

# Define RAG Proxy Agents for DM and Storyteller
ragproxyagent_dm = RetrieveUserProxyAgent(
    name="ragproxy_dm",
    human_input_mode="NEVER",
    retrieve_config={
        "task": "qa",
        "docs_path": [
            "../resources/dm_resources",
        ],
        "client": chroma_client_dm,
        "embedding_model": "all-mpnet-base-v2",
        "get_or_create": True,
    },
    code_execution_config=False,
)

ragproxyagent_st = RetrieveUserProxyAgent(
    name="ragproxy_st",
    human_input_mode="NEVER",
    retrieve_config={
        "task": "qa",
        "docs_path": [
            "../resources/st_resources",
        ],
        "client": chroma_client_st,
        "embedding_model": "all-mpnet-base-v2",
        "get_or_create": True,
    },
    code_execution_config=False,
)


# Instantiate agents
agents = {}

# Initialize Conversable DM and Storyteller Agents (AssistantAgents)
dm_agent = ConversableAgent(
    name="DMAgent",
    system_message=(
        "You are the Dungeon Master in a Dungeons and Dragons campaign, guiding a single player through an immersive storytelling experience."
    ),
    llm_config=llm_config,
    human_input_mode="NEVER",
    code_execution_config=False,
)



storyteller_agent = ConversableAgent(
    name="StorytellerAgent",
    system_message=(
        "You are an expert in storyline management for a Dungeons and Dragons role-playing campaign. "
        "Your role is to objectively evaluate the storyline and its components, not to narrate or lead the story. "
        "Provide feedback on the narrative structure, character development, and plot consistency. "
        "Identify strengths and weaknesses in the story and suggest improvements while remaining neutral. "
        "Your insights should help the DM enhance the overall storytelling experience for the player."
    ),
    llm_config=llm_config,
    human_input_mode="NEVER",
    code_execution_config=False,
)


# Register the Opal model client if LLM_PROVIDER is Opal
if LLM_PROVIDER == "opal":
    dm_agent.register_model_client(model_client_cls=CustomModelClient)
    storyteller_agent.register_model_client(model_client_cls=CustomModelClient)

# Register the agents in the dictionary
agents["DMAgent"] = dm_agent
agents["StorytellerAgent"] = storyteller_agent
