# llm/agents.py

import logging
import os

import chromadb
from autogen import ConversableAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from chromadb.utils import embedding_functions

# Import configurations based on LLM provider
from llm.llm_config import LLM_PROVIDER, llm_config, llm_config_DM, llm_config_ST

# ============================
# Logging Configuration
# ============================

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize ChromaDB clients for DM and Storyteller agents
CHROMA_DB_PATH_DM = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chromadb_dm"))
CHROMA_DB_PATH_ST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chromadb_st"))
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
        "docs_path": ["../resources/dm_resources"],
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
        "docs_path": ["../resources/st_resources"],
        "client": chroma_client_st,
        "embedding_model": "all-mpnet-base-v2",
        "get_or_create": True,
    },
    code_execution_config=False,
)

# Select LLM configuration for DM and Storyteller based on provider
if LLM_PROVIDER == "openai":
    llm_config_dm = llm_config_DM
    llm_config_st = llm_config_ST
else:
    llm_config_dm = llm_config
    llm_config_st = llm_config

# Initialize Conversable DM and Storyteller Agents
dm_agent = ConversableAgent(
    name="DMAgent",
    system_message=(
        "You are the Dungeon Master (DM) in a Dungeons & Dragons 5th Edition campaign, guiding a single player through an immersive and engaging storytelling experience. "
        "Your responsibilities include creating consistent, coherent narratives that align with the player's preferences and the previous storyline. "
        "Always follow the instructions provided in the prompts, and ensure that your responses are in the required JSON format. "
        "Do not include any text outside of the JSON block. "
        "Do not ask the player any questions; instead, use the provided context and previous storyline to craft the next scene."
    ),
    llm_config=llm_config_dm,
    human_input_mode="NEVER",
    code_execution_config=False,
)

storyteller_agent = ConversableAgent(
    name="StorytellerAgent",
    system_message=(
        "You are a Storytelling Expert for a Dungeons & Dragons 5th Edition campaign. "
        "Your role is to objectively evaluate the campaign storyline, ensuring it aligns with the player's preferences and maintains consistency with previous events. "
        "Provide constructive feedback on narrative structure, character development, plot consistency, and adherence to the player's preferences. "
        "Do not introduce new story elements or narrate the story. "
        "Always respond in the required JSON format. "
        "Do not include any text outside of the JSON block."
    ),
    llm_config=llm_config_st,
    human_input_mode="NEVER",
    code_execution_config=False,
)

# Register the agents in the dictionary
agents = {
    "DMAgent": dm_agent,
    "StorytellerAgent": storyteller_agent,
}
