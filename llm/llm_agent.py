# llm_agent.py

# ============================
# Imports and Dependencies
# ============================

import json
import logging
import re  # For extracting JSON
from typing import Any, Dict, List, Optional

import urllib3
from colorama import Fore, Style

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
    logger.debug(f"{Fore.MAGENTA}Parsing response from {Fore.BLUE}{agent_name}: {Fore.GREEN}{response}{Style.RESET_ALL}")

    try:
        json_str = extract_json_from_text(response)

        if json_str:
            parsed_json = json.loads(json_str)
            logger.debug(f"{Fore.MAGENTA}Parsed JSON response from {Fore.BLUE}{agent_name}: {Fore.GREEN}{parsed_json}{Style.RESET_ALL}")
            return parsed_json
        else:
            logger.error(
                f"{Fore.RED}No valid JSON found in response from {agent_name}. Using raw response.{Style.RESET_ALL}"
            )
            return {"raw_response": response}
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"{Fore.RED}Failed to parse JSON from {agent_name}. Error: {e}{Style.RESET_ALL}")
        return None


async def send_feedback_and_retry(
    agent_name: str, expected_keys: List[str], response: str
) -> Optional[List[Any]]:
    """
    Sends feedback to the agent and attempts to retrieve a corrected response.

    :param agent_name: The name of the agent sending the response.
    :param expected_keys: The keys expected in the corrected response JSON.
    :param response: The original response from the agent.
    """

    feedback_msg = format_feedback_prompt(expected_keys, response)

    logger.debug(f"{Fore.MAGENTA}Sending feedback to {Fore.BLUE}{agent_name}: {Fore.MAGENTA}{feedback_msg}{Style.RESET_ALL}")
    agent = AGENTS.get(agent_name)

    if not agent:
        logger.error(f"{Fore.RED}Agent '{agent_name}' not found.{Style.RESET_ALL}")
        return None

    feedback_response = await agent.generate_reply(feedback_msg)

    logger.debug(f"{Fore.MAGENTA}Raw feedback response from {Fore.BLUE}{agent_name}: {Fore.GREEN}{feedback_response}{Style.RESET_ALL}")
    parsed_feedback = await parse_response(agent_name, feedback_response)

    if parsed_feedback and isinstance(parsed_feedback, dict):
        # Extract values for the expected keys
        extracted = [parsed_feedback.get(key) for key in expected_keys if key in parsed_feedback]

        # Check if all extracted values are None (i.e., expected keys are missing)
        if not any(extracted) and "raw_response" in parsed_feedback:
            raw_response = parsed_feedback["raw_response"]
            extracted.append(raw_response)
            logger.debug(f"{Fore.MAGENTA}Added 'raw_response' to extracted as a fallback.{Style.RESET_ALL}")

        logger.debug(f"{Fore.MAGENTA}Extracted values: {Fore.BLUE}{extracted}{Style.RESET_ALL}")
        return extracted
    else:
        logger.error(
            f"{Fore.RED}Invalid feedback format from {agent_name}. Feedback response: {parsed_feedback}"
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
        logger.error(f"{Fore.RED}Agent '{agent_name}' not found.{Style.RESET_ALL}")
        return None

    retries = 0
    while retries < max_retries:
        response = ""
        try:
            logger.debug(
                f"{Fore.MAGENTA}Attempt {retries + 1}/{max_retries} - Sending prompt to {Fore.BLUE}{agent_name}: {Fore.MAGENTA}{prompt}{Style.RESET_ALL}"
            )
            response = agent.generate_reply(messages=prompt)

            if hasattr(response, "__await__"):
                response = await response

            logger.debug(f"{Fore.MAGENTA}Raw response from {Fore.BLUE}{agent_name}: {Fore.GREEN}{response}{Style.RESET_ALL}")

            # Ensure response is correctly parsed as JSON
            parsed_response = await parse_response(agent_name, response)

            return parsed_response

        except Exception as e:
            logger.error(
                f"{Fore.RED}Exception during response handling from {agent_name} on attempt {retries + 1}. Error: {e}{Style.RESET_ALL}"
            )

        retries += 1
        logger.debug(f"{Fore.MAGENTA}Sending feedback and trying again.{Style.RESET_ALL}")
        extracted = await send_feedback_and_retry(agent_name, expected_keys, response)

        if extracted:
            logger.debug(
                f"{Fore.MAGENTA}Successfully extracted {Fore.BLUE}{expected_keys}.{Style.RESET_ALL}"
            )
            return extracted
        else:
            logger.warning(f"{Fore.YELLOW}Feedback retry failed on attempt {retries}/{max_retries}{Style.RESET_ALL}")

    logger.error(
        f"{Fore.RED}Max retries reached for {agent_name}. Could not parse the response after {max_retries} attempts.{Style.RESET_ALL}"
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
            f"{Fore.MAGENTA}Handling inconsistent storyline, attempt {retries + 1}/{max_retries}{Style.RESET_ALL}"
        )
        revised_response = await get_agent_response(
            "DMAgent", dm_prompt, ["revised_storyline", "dm_response"]
        )

        # Check if revised_response contains the expected keys or fallback to "raw_response"
        if revised_response and isinstance(revised_response, dict):
            revised_storyline = revised_response.get("revised_storyline") or revised_response.get("raw_response") or ""
            dm_response_text = revised_response.get("dm_response") or revised_response.get("raw_response") or ""
        else:
            revised_storyline = ""
            dm_response_text = ""

        if dm_response_text:
            return revised_storyline

        retries += 1

    logger.error(
        f"{Fore.RED}Max retries reached for handling inconsistent storyline. Could not parse the response.{Style.RESET_ALL}"
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
        logger.debug(f"{Fore.MAGENTA}Starting a new campaign.")
        dm_prompt_content = create_campaign_prompt(user_input, user_preferences)
        dm_prompt = [{"role": "DMAgent", "content": dm_prompt_content}]

        dm_response = await get_agent_response(
            "DMAgent", dm_prompt, ["dm_response", "storyline"]
        )
        logger.debug(f"{Fore.MAGENTA}DM Agent response:\n{Fore.GREEN}{dm_response}{Style.RESET_ALL}")
        if not dm_response:
            logger.warning(f"{Fore.YELLOW}No DM Agent response found.{Style.RESET_ALL}")
            return {
                "dm_response": "Error starting a new campaign.",
                "full_storyline": storyline,
            }
        # Check if dm_response contains expected keys, else fallback to "raw_response"
        if isinstance(dm_response, dict):
            dm_response_text = dm_response.get("dm_response") or dm_response.get("raw_response") or ""
            new_storyline = dm_response.get("storyline") or dm_response.get("raw_response") or ""
        else:
            logger.error(f"{Fore.RED}Could not generate campaign. Unknown error.{Style.RESET_ALL}")
            return {
                "dm_response": "Error starting a new campaign.",
                "full_storyline": storyline,
            }

        logger.debug(f"{Fore.MAGENTA}New Storyline: {new_storyline}")

        storyteller_prompt_content = validate_storyline_prompt(
            context, new_storyline, user_preferences
        )
        storyteller_prompt = [
            {"role": "StorytellerAgent", "content": storyteller_prompt_content}
        ]

        storyteller_response = await get_agent_response(
            "StorytellerAgent", storyteller_prompt, ["consistency_check", "feedback"]
        )

        # Only proceed with feedback handling if expected keys are present
        if (
                storyteller_response
                and isinstance(storyteller_response, dict)
                and "consistency_check" in storyteller_response
                and "feedback" in storyteller_response
        ):
            if storyteller_response["consistency_check"] == "Yes":
                storyline += new_storyline
                return {"dm_response": dm_response_text, "full_storyline": storyline}
            else:
                feedback = storyteller_response["feedback"]
                dm_inconsistency_prompt_content = revise_campaign_prompt(
                    context, new_storyline, feedback, user_preferences
                )
                dm_inconsistency_prompt = [
                    {"role": "DMAgent", "content": dm_inconsistency_prompt_content}
                ]

                # Get the response from handle_inconsistent_storyline
                dm_revision_response = await handle_inconsistent_storyline(dm_inconsistency_prompt)

                # Check if dm_revision_response contains expected keys, else fallback to "raw_response"
                if isinstance(dm_revision_response, dict):
                    revised_storyline = dm_revision_response.get("revised_storyline") or dm_revision_response.get(
                        "raw_response") or ""
                    dm_revision_text = dm_revision_response.get("dm_response") or dm_revision_response.get(
                        "raw_response") or ""
                else:
                    revised_storyline = ""
                    dm_revision_text = ""

                # Append revised storyline if available
                storyline += revised_storyline

                return {
                    "dm_response": dm_revision_text or "Error in processing the revision response.",
                    "full_storyline": storyline,
                }

        else:
            storyline += new_storyline
            return {"dm_response": dm_response_text, "full_storyline": storyline}

    else:
        logger.debug("Ongoing campaign detected.")

        if not storyline:
            return {
                "dm_response": "Error continuing the campaign. No storyline found.",
                "full_storyline": "",
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
