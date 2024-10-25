import asyncio
import json
import logging

from llm.agents import (
    dm_agent,
)
from llm.prompts import dm_agent_prompt

# Configure the logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def parse_agent_response(agent_type, agent_response):
    """Parses the response from an agent and extracts relevant content based on agent type."""
    try:
        # Attempt to load the JSON response from the agent
        response_data = json.loads(agent_response)

        # Define what key to extract based on the agent type
        agent_response_key_map = {
            "DMAgent": "dm_response",
            "RuleExpertAgent": "rule_explanation",
            "StorytellerAgent": "storyteller_response",
            "AssistantAgent": "assistant_response",
        }

        # Check if the agent type is recognized and extract the correct key
        if agent_type in agent_response_key_map:
            response_key = agent_response_key_map[agent_type]
            if response_key in response_data:
                return response_data[
                    response_key
                ]  # Return the relevant response content
            else:
                logger.error(
                    f"Invalid {agent_type} response format: '{response_key}' key not found."
                )
                return (
                    f"An error occurred while processing the {agent_type}'s response."
                )
        else:
            logger.error(f"Unrecognized agent type: {agent_type}")
            return "An error occurred while processing the response."

    except json.JSONDecodeError:
        logger.error(f"Failed to parse {agent_type} response as JSON.")
        return "An error occurred while processing the response."


async def generate_gm_response(user_input, conversation_history, user_preferences):
    if not isinstance(user_input, str):
        logger.error("Invalid user input provided.")
        return "Invalid input. Please enter a valid command."

    if not isinstance(user_preferences, dict):
        logger.error("Invalid user preferences provided.")
        user_preferences = {}

    logger.info(f"User input: {user_input}")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Build context from conversation history
    context = ""
    if conversation_history and isinstance(conversation_history, list):
        for message in conversation_history[-6:]:
            role = message.get("role")
            content = message.get("content")
            if role and content:
                role = "Player" if role == "user" else "GM"
                context += f"{role}: {content}\n"
            else:
                logger.warning("Invalid message format in conversation history.")
    else:
        logger.warning("Conversation history is empty or invalid.")

    logger.debug(f"Conversation context built:\n{context}")

    # Include user preferences
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    logger.debug(f"User preferences:\n{preferences_text}")

    # Use the dm_agent_prompt to create the input prompt for the DM agent
    dm_prompt = dm_agent_prompt(context, user_input)
    dm_messages = [{"role": "user", "content": dm_prompt}]
    logger.info("Routing message to DMAgent.")
    logger.debug(f"DMAgent prompt:\n{dm_prompt}")

    try:
        dm_response = await loop.run_in_executor(
            None, dm_agent.generate_reply, dm_messages
        )
        logger.debug(f"DMAgent response:\n{dm_response}")

        # Parse the DM agent's response using the flexible parse_agent_response function
        message_content = parse_agent_response("DMAgent", dm_response)

        # Return the message content to display to the user
        return message_content

    except Exception as e:
        logger.error(f"DMAgent.generate_reply failed: {e}", exc_info=True)
        return "An error occurred while generating the response. Please try again."
