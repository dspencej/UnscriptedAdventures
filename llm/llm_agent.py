# llm_agent.py

# ============================
# Imports and Dependencies
# ============================

import json
import logging
import re  # For extracting JSON
from typing import Any, Dict, List, Optional

import urllib3

from llm.agents import dm_agent, storyteller_agent
from llm.prompts import (
    continue_campaign_prompt,
    create_campaign_prompt,
    feedback_inconsistent_storyline,
    feedback_missing_storyline,
    format_feedback_prompt,
    revise_campaign_prompt,
    validate_storyline_prompt,
)

# ============================
# SSL Warning Suppression
# ============================

# Disable warnings related to insecure HTTPS requests made via urllib3.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================
# Logging Configuration
# ============================

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ============================
# Constants
# ============================

MAX_RETRIES = 3  # Maximum number of retries for handling inconsistencies

# ============================
# Agent Registration
# ============================

AGENTS = {
    "DMAgent": dm_agent,
    "StorytellerAgent": storyteller_agent,
    # Add more agents as needed in the future, e.g.:
    # "LoreAgent": lore_agent,
    # "CombatAgent": combat_agent,
}


# ============================
# Helper Functions
# ============================


async def parse_response(agent_name: str, response: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract and parse a JSON object from a text response.
    """
    logger.debug(f"Parsing response from {agent_name}: {response}")

    try:
        json_str = extract_json_from_text(response)
        logger.debug(f"Extracted JSON string from {agent_name}: {json_str}")

        if json_str:
            parsed_json = json.loads(json_str)
            logger.debug(f"Successfully parsed JSON response from {agent_name}.")
            return parsed_json
        else:
            logger.error(
                f"No valid JSON found in response from {agent_name}. Returning raw response."
            )
            return {"raw_response": response}
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse JSON from {agent_name}. Error: {e}")
        return None


async def send_feedback_and_retry(
    agent_name: str, expected_keys: List[str], issue: Optional[str] = None
) -> Optional[List[Any]]:
    """
    Sends feedback to the agent and attempts to retrieve a corrected response.

    Args:
        agent_name (str): The name of the agent sending the response.
        expected_keys (list): The keys expected in the corrected response JSON.
        issue (str): A specific issue, if any (e.g., missing storyline, inconsistency).

    Returns:
        list or None: Extracted values from the corrected response, or None if feedback fails.
    """
    # Trigger specific feedback based on the issue
    if issue == "missing_storyline":
        feedback_msg = feedback_missing_storyline(agent_name)
    elif issue == "inconsistent_storyline":
        feedback_msg = feedback_inconsistent_storyline(
            agent_name, "Storyline lacks consistency."
        )
    else:
        # Default feedback for invalid format or general issue
        feedback_msg = format_feedback_prompt(agent_name)

    logger.debug(f"Sending feedback to {agent_name}: {feedback_msg}")
    agent = AGENTS.get(agent_name)

    if not agent:
        logger.error(f"Agent '{agent_name}' not found.")
        return None

    feedback_response = await agent.generate_reply(feedback_msg)

    logger.debug(f"Raw feedback response from {agent_name}: {feedback_response}")
    parsed_feedback = await parse_response(agent_name, feedback_response)

    if parsed_feedback and isinstance(
        parsed_feedback, dict
    ):  # Ensure it's a dictionary
        extracted = [parsed_feedback.get(key) for key in expected_keys]
        logger.debug(f"Extracted {expected_keys} from feedback response.")
        return extracted
    else:
        logger.error(
            f"Failed to parse feedback response from {agent_name}. Feedback response: {parsed_feedback}"
        )
        return None


async def get_agent_response(
    agent_name: str,
    prompt: List[Dict[str, str]],
    expected_keys: List[str],
    max_retries: int = MAX_RETRIES,
) -> Optional[List[Any]]:
    """
    Sends a prompt to the specified agent and retrieves the expected keys from the response.
    Continuously attempts to parse the response until MAX_RETRIES is reached. If parsing fails,
    sends a feedback message and retries.
    """
    agent = AGENTS.get(agent_name)
    if not agent:
        logger.error(f"Agent '{agent_name}' not found.")
        return None

    retries = 0
    while retries < max_retries:
        try:
            logger.debug(
                f"Attempt {retries + 1}/{max_retries} - Sending prompt to {agent_name}"
            )
            response = agent.generate_reply(messages=prompt)

            if hasattr(response, "__await__"):  # Check if it's awaitable
                response = await response

            logger.debug(f"Raw response from {agent_name}: {response}")

            # Ensure response is correctly parsed as JSON
            parsed_response = await parse_response(agent_name, response)

            if parsed_response and isinstance(
                parsed_response, dict
            ):  # Check if parsed response is a dict
                extracted = [
                    parsed_response.get(key, "") for key in expected_keys
                ]  # Get keys or return empty strings
                logger.debug(
                    f"Successfully extracted {expected_keys} from {agent_name} response: {extracted}"
                )
                return extracted
            else:
                logger.warning(
                    f"Failed to parse response from {agent_name}. Attempt {retries + 1}/{max_retries}"
                )

        except Exception as e:
            logger.error(
                f"Exception during response handling from {agent_name} on attempt {retries + 1}. Error: {e}"
            )

        retries += 1
        logger.debug(f"Retrying after feedback, attempt {retries}/{max_retries}")
        extracted = await send_feedback_and_retry(agent_name, expected_keys)

        if extracted:
            logger.debug(
                f"Successfully extracted {expected_keys} from feedback response on attempt {retries}"
            )
            return extracted
        else:
            logger.warning(f"Feedback retry failed on attempt {retries}/{max_retries}")

    logger.error(
        f"Max retries reached for {agent_name}. Could not parse the response after {max_retries} attempts."
    )
    return None


def extract_json_from_text(response: str) -> Optional[str]:
    """
    Attempts to extract a JSON object from a text block, checking for '```json' first,
    and if not found, checking for JSON-like content enclosed in curly braces.
    """
    logger.debug("Attempting to extract JSON block from response.")

    # Step 1: Look for a JSON block enclosed in ```json ... ```
    json_block_pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(json_block_pattern, response, re.DOTALL)

    if match:
        json_str = match.group(1)
        try:
            json_str = re.sub(
                r"[\x00-\x1F\x7F]", "", json_str
            )  # Clean up control characters
            return json_str
        except Exception as e:
            logger.error(f"Error cleaning JSON block: {e}")
            return None

    # Step 2: If no JSON block found, check for JSON-like content using curly braces
    logger.debug("No valid JSON block found, checking for JSON-like content.")
    json_pattern = r"(\{.*?\})"
    match = re.search(json_pattern, response, re.DOTALL)

    if match:
        json_str = match.group(1)
        try:
            json_str = re.sub(r"[\x00-\x1F\x7F]", "", json_str)
            return json_str
        except Exception as e:
            logger.error(f"Error cleaning JSON-like content: {e}")
            return None

    logger.error("No valid JSON found in the response after multiple attempts.")
    return None


def build_conversation_context(
    conversation_history: List[Dict[str, str]], user_preferences: Dict[str, str]
) -> str:
    """
    Builds a conversation context string from the conversation history.
    """
    context = ""
    for message in conversation_history:
        if "user" in message:
            context += f"User: {message['user']}\n"
        if "dm" in message:
            context += f"DM: {message['dm']}\n"

    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    context += f"**User Preferences:**\n{preferences_text}\n"
    return context


async def handle_inconsistent_storyline(
    dm_prompt: List[Dict[str, str]], max_retries: int = MAX_RETRIES
) -> str:
    """
    Handles inconsistent storyline by sending the inconsistency prompt to the DM Agent.
    """
    retries = 0
    while retries < max_retries:
        logger.debug(
            f"Handling inconsistent storyline, attempt {retries + 1}/{max_retries}"
        )
        revised_response = await get_agent_response(
            "DMAgent", dm_prompt, ["revised_storyline", "dm_response"]
        )

        if revised_response and revised_response[0]:
            return revised_response[1]

        retries += 1
        logger.error(
            f"Failed to parse revised storyline from DMAgent (Attempt {retries}/{max_retries}). Sending feedback."
        )

        feedback_msg = feedback_inconsistent_storyline(
            "DMAgent", "The storyline has inconsistencies."
        )
        feedback_response = await get_agent_response(
            "DMAgent", feedback_msg, ["revised_storyline", "dm_response"]
        )

        if feedback_response and feedback_response[0]:
            return feedback_response[1]

    logger.error(
        "Max retries reached for handling inconsistent storyline. Could not parse the response."
    )
    return "Failed to resolve inconsistencies after multiple attempts. Please adjust your input and try again."


# ============================
# Main Function
# ============================
async def generate_gm_response(
    user_input: str,
    conversation_history: List[Dict[str, str]],
    user_preferences: Dict[str, str],
    storyline: str,
) -> Dict[str, str]:
    """
    Manages the workflow for starting or continuing a campaign, including communication between agents.
    """
    logger.debug("Generating GM response.")
    is_new_campaign = not conversation_history or len(conversation_history) == 0
    context = build_conversation_context(conversation_history, user_preferences)
    logger.debug(f"Conversation context:\n{context}")

    if not storyline:
        storyline = ""

    if is_new_campaign:
        logger.debug("Starting a new campaign.")
        dm_prompt_content = create_campaign_prompt(user_input, user_preferences)
        dm_prompt = [{"role": "DMAgent", "content": dm_prompt_content}]

        dm_response = await get_agent_response(
            "DMAgent", dm_prompt, ["dm_response", "storyline"]
        )
        if not dm_response:
            return {
                "dm_response": "Error starting a new campaign.",
                "full_storyline": storyline,
            }

        new_storyline = dm_response[1] or ""  # Accept an empty storyline
        storyline += new_storyline
        dm_response_text = dm_response[0]

        storyteller_prompt_content = validate_storyline_prompt(
            context, storyline, user_preferences
        )
        storyteller_prompt = [
            {"role": "StorytellerAgent", "content": storyteller_prompt_content}
        ]

        storyteller_response = await get_agent_response(
            "StorytellerAgent", storyteller_prompt, ["consistency_check", "feedback"]
        )

        if storyteller_response and storyteller_response[0] == "Yes":
            return {"dm_response": dm_response_text, "full_storyline": storyline}
        else:
            feedback = (
                storyteller_response[1]
                if storyteller_response
                else "No feedback provided."
            )
            dm_inconsistency_prompt_content = revise_campaign_prompt(
                context, feedback, user_preferences
            )
            dm_inconsistency_prompt = [
                {"role": "DMAgent", "content": dm_inconsistency_prompt_content}
            ]
            return {
                "dm_response": await handle_inconsistent_storyline(
                    dm_inconsistency_prompt
                ),
                "full_storyline": storyline,
            }

    else:
        logger.debug("Ongoing campaign detected.")

        if not storyline:
            return {
                "dm_response": "Error continuing the campaign. No storyline found.",
                "full_storyline": None,
            }

        dm_continue_prompt_content = continue_campaign_prompt(
            context, storyline, user_input, user_preferences
        )
        dm_continue_prompt = [
            {"role": "DMAgent", "content": dm_continue_prompt_content}
        ]

        dm_response = await get_agent_response(
            "DMAgent", dm_continue_prompt, ["dm_response", "storyline"]
        )
        if not dm_response:
            return {
                "dm_response": "Error continuing the campaign.",
                "full_storyline": storyline,
            }

        new_storyline = dm_response[1] or ""  # Accept empty storyline
        storyline += "\n\n" + new_storyline
        dm_response_text = dm_response[0]

        storyteller_continue_prompt = validate_storyline_prompt(
            context, storyline, user_preferences
        )
        storyteller_continue_prompt = [
            {"role": "StorytellerAgent", "content": storyteller_continue_prompt}
        ]

        storyteller_response = await get_agent_response(
            "StorytellerAgent",
            storyteller_continue_prompt,
            ["consistency_check", "feedback"],
        )

        if storyteller_response and storyteller_response[0] == "Yes":
            return {"dm_response": dm_response_text, "full_storyline": storyline}
        else:
            feedback = (
                storyteller_response[1]
                if storyteller_response
                else "No feedback provided."
            )
            dm_inconsistency_prompt_content = revise_campaign_prompt(
                context, feedback, user_preferences
            )
            dm_inconsistency_prompt = [
                {"role": "DMAgent", "content": dm_inconsistency_prompt_content}
            ]
            return {
                "dm_response": await handle_inconsistent_storyline(
                    dm_inconsistency_prompt
                ),
                "full_storyline": storyline,
            }
