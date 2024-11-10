# llm/agents.py

import logging
import os
from typing import Dict, Any

import chromadb
from autogen import ConversableAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from chromadb.utils import embedding_functions

# Import configurations based on LLM provider

# ============================
# Logging Configuration
# ============================

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ============================
# Constants
# ============================

# Paths for ChromaDB storage
CHROMA_DB_PATH_DM = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "chromadb_dm")
)
CHROMA_DB_PATH_ST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "chromadb_st")
)

# Initialize ChromaDB clients
chroma_client_dm = chromadb.PersistentClient(path=CHROMA_DB_PATH_DM)
chroma_client_st = chromadb.PersistentClient(path=CHROMA_DB_PATH_ST)

# Initialize embedding function for retrieval
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)


# ============================
# Helper Functions
# ============================


def create_ragproxyagent(agent_type: str) -> RetrieveUserProxyAgent:
    """
    Factory function to create a RetrieveUserProxyAgent based on the agent type.

    :param agent_type: Type of the agent ('dm' or 'st')
    :return: Configured RetrieveUserProxyAgent instance
    """
    if agent_type == "dm":
        client = chroma_client_dm
        docs_path = ["../resources/dm_resources"]
    elif agent_type == "st":
        client = chroma_client_st
        docs_path = ["../resources/st_resources"]
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    return RetrieveUserProxyAgent(
        name=f"ragproxy_{agent_type}",
        human_input_mode="NEVER",
        retrieve_config={
            "task": "qa",
            "docs_path": docs_path,
            "client": client,
            "embedding_model": "all-mpnet-base-v2",
            "get_or_create": True,
        },
        code_execution_config=False,
    )


# ============================
# Agent Factory Functions
# ============================


def create_dm_agent(llm_config: Dict[str, Any]) -> ConversableAgent:
    """
    Factory function to create a Game Master (GM) ConversableAgent.

    :param llm_config: Configuration dictionary for the LLM
    :return: Configured ConversableAgent instance for DM
    """

    dm_agent = ConversableAgent(
        name="DMAgent",
        system_message=(
            "You are the Game Master (GM) in a campaign for the world's Most Popular role playing game (5th Edition), "
            "guiding a single player"
            "through an immersive and engaging storytelling experience."
            "Your responsibilities include creating consistent, coherent narratives that align with the player's "
            "preferences and the previous storyline."
            "Always follow the instructions provided in the prompts, and ensure that your responses are in the "
            "required JSON format."
            "Do not include any text outside of the JSON block. "
            "Do not ask the player any questions; instead, use the provided context and previous storyline to craft "
            "the next scene."
        ),
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    return dm_agent


def create_storyteller_agent(llm_config: Dict[str, Any]) -> ConversableAgent:
    """
    Factory function to create a Storyteller ConversableAgent.

    :param llm_config: Configuration dictionary for the LLM
    :return: Configured ConversableAgent instance for Storyteller
    """

    storyteller_agent = ConversableAgent(
        name="StorytellerAgent",
        system_message=(
            "You are a Storytelling Expert for a campaign in the world's Most Popular role playing game (5th Edition)"
            "Your role is to objectively evaluate the campaign storyline, ensuring it aligns with the player's "
            "preferences and maintains consistency with previous events."
            "Provide constructive feedback on narrative structure, character development, plot consistency, "
            "and adherence to the player's preferences."
            "Do not introduce new story elements or narrate the story. "
            "Always respond in the required JSON format. "
            "Do not include any text outside of the JSON block."
        ),
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    return storyteller_agent


# ============================
# Agent Registration
# ============================


def get_agents(llm_config: Dict[str, Any]) -> Dict[str, ConversableAgent]:
    """
    Retrieves agent instances based on the specified LLM configuration.

    :param llm_config: The LLM configuration dictionary
    :return: Dictionary of agent instances
    """
    try:
        # Create agent instances with the fetched configurations
        dm_agent = create_dm_agent(llm_config)
        storyteller_agent = create_storyteller_agent(llm_config)
    except Exception as e:
        logger.error(f"Error creating agents: {e}")
        raise

    # Return agents in a dictionary
    return {
        "DMAgent": dm_agent,
        "StorytellerAgent": storyteller_agent,
    }
