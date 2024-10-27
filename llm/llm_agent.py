# ============================
# Imports and Dependencies
# ============================

import json
import logging
import re
from typing import Any, Dict, List, Optional

import urllib3
from colorama import Fore, Style

from llm.agents import dm_agent, storyteller_agent
from llm.prompts import (
    continue_campaign_prompt,
    create_campaign_prompt,
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

# ============================
# Helper Functions
# ============================


async def parse_response(agent_name: str, response: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract and parse a JSON object from a text response.
    """
    logger.debug(
        f"{Fore.MAGENTA}[PARSING] Response from {Fore.BLUE}{agent_name}: {Fore.GREEN}{response}{Style.RESET_ALL}"
    )

    try:
        json_str = extract_json_from_text(response)

        if json_str:
            parsed_json = json.loads(json_str)
            logger.debug(
                f"{Fore.MAGENTA}[SUCCESS] Parsed JSON from {Fore.BLUE}{agent_name}: {Fore.GREEN}{parsed_json}{Style.RESET_ALL}"
            )
            return parsed_json
        else:
            logger.warning(
                f"{Fore.YELLOW}[WARNING] No valid JSON found in response from {Fore.BLUE}{agent_name}. Using raw response.{Style.RESET_ALL}"
            )
            return {"raw_response": response}
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(
            f"{Fore.RED}[ERROR] Failed to parse JSON from {Fore.BLUE}{agent_name}. Error: {e}{Style.RESET_ALL}"
        )
        return None


async def send_feedback_and_retry(
    agent_name: str, expected_keys: List[str], response: str
) -> Optional[List[Any]]:
    """
    Sends feedback to the agent and attempts to retrieve a corrected response.
    """
    # Generate the feedback message content
    feedback_msg_content = format_feedback_prompt(expected_keys, response)

    # Format the feedback prompt with 'system' role to instruct the agent
    feedback_prompt = [{"role": "system", "content": feedback_msg_content}]

    logger.debug(
        f"{Fore.MAGENTA}[FEEDBACK] Sending feedback to {Fore.BLUE}{agent_name}: {Fore.MAGENTA}{feedback_msg_content}{Style.RESET_ALL}"
    )

    agent = AGENTS.get(agent_name)

    if not agent:
        logger.error(
            f"{Fore.RED}[ERROR] Agent '{agent_name}' not found.{Style.RESET_ALL}"
        )
        return None

    # Send the feedback prompt and await the corrected response
    feedback_response = agent.generate_reply(feedback_prompt)

    # Check if response is a coroutine and await it if necessary
    if hasattr(feedback_response, "__await__"):
        feedback_response = await feedback_response

    logger.debug(
        f"{Fore.MAGENTA}[FEEDBACK RESPONSE] Raw response from {Fore.BLUE}{agent_name}: {Fore.GREEN}{feedback_response}{Style.RESET_ALL}"
    )

    parsed_feedback = await parse_response(agent_name, feedback_response)

    if parsed_feedback and isinstance(parsed_feedback, dict):
        extracted = [
            parsed_feedback.get(key) for key in expected_keys if key in parsed_feedback
        ]

        if not any(extracted) and "raw_response" in parsed_feedback:
            raw_response = parsed_feedback["raw_response"]
            extracted.append(raw_response)
            logger.debug(
                f"{Fore.MAGENTA}[FALLBACK] Added 'raw_response' to extracted values.{Style.RESET_ALL}"
            )

        logger.debug(
            f"{Fore.MAGENTA}[EXTRACTED] Values extracted: {Fore.BLUE}{extracted}{Style.RESET_ALL}"
        )
        return extracted
    else:
        logger.error(
            f"{Fore.RED}[ERROR] Invalid feedback format from {Fore.BLUE}{agent_name}. Feedback response: {parsed_feedback}{Style.RESET_ALL}"
        )
        return None


async def get_agent_response(
    agent_name: str,
    prompt: List[Dict[str, str]],
    expected_keys: List[str],
    max_retries: int = MAX_RETRIES,
) -> None | dict | list[Any]:
    """
    Sends a prompt to the specified agent and retrieves the expected keys from the response.
    Retries the process up to max_retries times if the response is not valid JSON or is missing expected keys.
    """
    agent = AGENTS.get(agent_name)

    if not agent:
        logger.error(
            f"{Fore.RED}[ERROR] Agent '{agent_name}' not found.{Style.RESET_ALL}"
        )
        return None

    retries = 0
    while retries < max_retries:
        response = ""
        try:
            logger.debug(
                f"{Fore.MAGENTA}[ATTEMPT {retries + 1}/{max_retries}] Sending prompt to {Fore.BLUE}{agent_name}: {Fore.MAGENTA}{prompt}{Style.RESET_ALL}"
            )
            response = agent.generate_reply(messages=prompt)

            # Check if response is a coroutine and await it if necessary
            if hasattr(response, "__await__"):
                response = await response

            logger.debug(
                f"{Fore.MAGENTA}[RECEIVED] Raw response from {Fore.BLUE}{agent_name}: {Fore.GREEN}{response}{Style.RESET_ALL}"
            )

            # Try to parse the response as JSON
            parsed_response = await parse_response(agent_name, response)

            # If it's not valid JSON or is missing keys, log a warning and proceed to retry
            if not parsed_response or not isinstance(parsed_response, dict):
                logger.warning(
                    f"{Fore.YELLOW}[WARNING] Invalid JSON format received from {Fore.BLUE}{agent_name}.{Style.RESET_ALL}"
                )
                raise ValueError(f"Invalid response format from {agent_name}")

            # Ensure all expected keys are present in the response
            missing_keys = [key for key in expected_keys if key not in parsed_response]
            if missing_keys:
                logger.warning(
                    f"{Fore.YELLOW}[WARNING] Missing expected keys in {Fore.BLUE}{agent_name}'s response: {missing_keys}.{Style.RESET_ALL}"
                )
                raise KeyError(
                    f"Expected key(s) '{missing_keys}' missing in {agent_name}'s response"
                )

            # If everything is valid, return the parsed response
            return parsed_response

        except (ValueError, KeyError) as e:
            # Log the exception and proceed to retry with feedback
            logger.error(
                f"{Fore.RED}[EXCEPTION] {str(e)} Error handling response from {Fore.BLUE}{agent_name} on attempt {retries + 1}.{Style.RESET_ALL}"
            )

        # If there was an error, provide feedback and retry
        retries += 1
        logger.debug(
            f"{Fore.MAGENTA}[RETRY] Sending feedback and attempting retry process.{Style.RESET_ALL}"
        )

        # Use the send_feedback_and_retry function to ask the agent to correct its response
        extracted = await send_feedback_and_retry(agent_name, expected_keys, response)

        if extracted:
            logger.debug(
                f"{Fore.MAGENTA}[SUCCESS] Successfully extracted {Fore.BLUE}{expected_keys}.{Style.RESET_ALL}"
            )
            return extracted
        else:
            logger.warning(
                f"{Fore.YELLOW}[RETRY FAILED] Attempt {retries}/{max_retries} failed.{Style.RESET_ALL}"
            )

    # If retries exhausted
    logger.error(
        f"{Fore.RED}[FAILURE] Max retries reached for {Fore.BLUE}{agent_name}. Could not parse the response after {max_retries} attempts.{Style.RESET_ALL}"
    )
    return None


def extract_json_from_text(response: str) -> Optional[str]:
    """
    Attempts to extract a JSON object from a text block.
    """
    logger.debug(
        f"{Fore.MAGENTA}[EXTRACT] Attempting to extract JSON from response.{Style.RESET_ALL}"
    )

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
            logger.error(
                f"{Fore.RED}[ERROR] Cleaning JSON block failed: {e}{Style.RESET_ALL}"
            )
            return None

    # Step 2: Check for JSON-like content
    logger.debug(
        f"{Fore.MAGENTA}[EXTRACT] No valid JSON block found, checking for JSON-like content.{Style.RESET_ALL}"
    )
    json_pattern = r"(\{.*?\})"
    match = re.search(json_pattern, response, re.DOTALL)

    if match:
        json_str = match.group(1)
        try:
            json_str = re.sub(r"[\x00-\x1F\x7F]", "", json_str)
            return json_str
        except Exception as e:
            logger.error(
                f"{Fore.RED}[ERROR] Cleaning JSON-like content failed: {e}{Style.RESET_ALL}"
            )
            return None

    logger.error(
        f"{Fore.RED}[ERROR] No valid JSON found in the response after multiple attempts.{Style.RESET_ALL}"
    )
    return None


def build_conversation_context(
    conversation_history: List[Dict[str, str]],
    user_preferences: Dict[str, str],
    current_character: Dict[str, Any],  # Added current_character argument
) -> str:
    """
    Builds a conversation context string from the conversation history, user preferences, and character details.
    """
    context = ""
    # Add conversation history
    for message in conversation_history:
        if "user" in message:
            context += f"User: {message['user']}\n"
        if "dm" in message:
            context += f"DM: {message['dm']}\n"

    # Add user preferences
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    context += f"**User Preferences:**\n{preferences_text}\n"

    # Add current character details
    if current_character:
        character_details = "\n".join(
            [
                f"- {key.capitalize()}: {value}"
                for key, value in current_character.items()
            ]
        )
        context += f"\n**Character Details:**\n{character_details}\n"

    return context


async def handle_storyline_feedback(
    dm_prompt: List[Dict[str, str]], max_retries: int = MAX_RETRIES
) -> Optional[Dict[str, Any]]:
    """
    Handles inconsistent storyline by sending the inconsistency prompt to the DM Agent.
    """
    retries = 0
    while retries < max_retries:
        logger.debug(
            f"{Fore.MAGENTA}[ATTEMPT {retries + 1}/{max_retries}] Handling storyline feedback.{Style.RESET_ALL}"
        )

        revised_response = await get_agent_response(
            "DMAgent", dm_prompt, ["dm_response"]
        )

        # Check if revised_response contains the expected keys or fallback to "raw_response"
        if revised_response and isinstance(revised_response, dict):
            dm_response_text = (
                revised_response.get("dm_response")
                or revised_response.get("raw_response")
                or ""
            )

            logger.debug(
                f"{Fore.MAGENTA}[SUCCESS] Received revised storyline from {Fore.BLUE}DMAgent{Style.RESET_ALL}: "
                f"{Fore.GREEN}{dm_response_text}{Style.RESET_ALL}"
            )

            if dm_response_text:
                logger.debug(
                    f"{Fore.MAGENTA}[RESOLVED] Storyline inconsistency resolved with revised response.{Style.RESET_ALL}"
                )
                return revised_response  # Return the entire dict, not just the dm_response_text

        else:
            logger.warning(
                f"{Fore.YELLOW}[WARNING] Invalid or incomplete response from {Fore.BLUE}DMAgent{Style.RESET_ALL}. Retrying...{Style.RESET_ALL}"
            )

        retries += 1

    logger.error(
        f"{Fore.RED}[FAILURE] Max retries reached while handling inconsistent storyline. Could not resolve the issue.{Style.RESET_ALL}"
    )
    return (
        None  # Return None or an appropriate fallback value when retries are exhausted
    )


# ============================
# Main Function
# ============================
async def generate_gm_response(
    user_input: str,
    conversation_history: List[Dict[str, str]],
    user_preferences: Dict[str, str],
    storyline: str,
    current_character: Dict[str, Any],
) -> Dict[str, str]:
    """
    Manages the workflow for starting or continuing a campaign, including communication between agents.
    """
    logger.debug(f"{Fore.MAGENTA}[START] Generating GM response.{Style.RESET_ALL}")
    is_new_campaign = not conversation_history or len(conversation_history) == 0
    context = build_conversation_context(
        conversation_history, user_preferences, current_character
    )
    logger.debug(
        f"{Fore.MAGENTA}[CONTEXT] Conversation context:\n{Fore.BLUE}{context}{Style.RESET_ALL}"
    )

    if not storyline:
        storyline = ""

    if is_new_campaign:
        logger.debug(
            f"{Fore.MAGENTA}[NEW CAMPAIGN] Starting a new campaign.{Style.RESET_ALL}"
        )
        dm_prompt_content = create_campaign_prompt(user_input, context)
        dm_prompt = [{"role": "DMAgent", "content": dm_prompt_content}]

        dm_response = await get_agent_response("DMAgent", dm_prompt, ["dm_response"])
        logger.debug(
            f"{Fore.MAGENTA}[EXTRACTED JSON] Extracted JSON from DM Response:\n{Fore.GREEN}{dm_response
            }{Style.RESET_ALL}"
        )

        if not dm_response:
            logger.warning(
                f"{Fore.YELLOW}[WARNING] No DM Agent response found.{Style.RESET_ALL}"
            )
            return {
                "dm_response": "Error starting a new campaign.",
                "full_storyline": storyline,
            }

        # Check if dm_response contains expected keys, else fallback to "raw_response"
        if isinstance(dm_response, dict):
            dm_response_text = (
                dm_response.get("dm_response") or dm_response.get("raw_response") or ""
            )
        else:
            logger.error(
                f"{Fore.RED}[ERROR] Could not generate campaign. Unknown error.{Style.RESET_ALL}"
            )
            return {
                "dm_response": "Error starting a new campaign.",
                "full_storyline": storyline,
            }
        logger.debug(
            f"{Fore.MAGENTA}[DM RESPONSE] Extracted DM Agent response:\n{Fore.GREEN}{dm_response_text}{Style.RESET_ALL}"
        )

        storyteller_prompt_content = validate_storyline_prompt(
            context, dm_response_text
        )
        storyteller_prompt = [
            {"role": "StorytellerAgent", "content": storyteller_prompt_content}
        ]

        storyteller_response = await get_agent_response(
            "StorytellerAgent", storyteller_prompt, ["feedback"]
        )
        logger.debug(
            f"{Fore.MAGENTA}[STORYTELLER RESPONSE] Parsed Storyteller Agent response:\n{Fore.GREEN}{storyteller_response}{Style.RESET_ALL}"
        )

        # Only proceed if feedback is present
        if storyteller_response and isinstance(storyteller_response, dict):
            feedback = storyteller_response.get("feedback", "")

            logger.debug(
                f"{Fore.MAGENTA}[STORYTELLER FEEDBACK] Feedback received: {feedback}{Style.RESET_ALL}"
            )

            # Create a DM revision prompt based on the feedback
            dm_feedback_prompt_content = revise_campaign_prompt(
                context, dm_response_text, feedback
            )
            dm_feedback_prompt = [
                {"role": "DMAgent", "content": dm_feedback_prompt_content}
            ]

            # Get the response from handle_inconsistent_storyline
            dm_revision_response = await handle_storyline_feedback(dm_feedback_prompt)

            # Extract revised response
            if isinstance(dm_revision_response, dict):
                dm_revision_text = dm_revision_response.get("dm_response", "")
                if not dm_revision_text:
                    logger.error(
                        f"{Fore.RED}[ERROR] Missing dm_response in the revised response from DMAgent.{Style.RESET_ALL}"
                    )
            else:
                dm_revision_text = ""
                logger.error(
                    f"{Fore.RED}[ERROR] Invalid or missing revised response from DMAgent.{Style.RESET_ALL}"
                )

            logger.debug(
                f"{Fore.MAGENTA}[REVISED STORYLINE] Revised storyline after feedback: {dm_revision_text}{Style.RESET_ALL}"
            )

            # Ensure the revised storyline is appended only if valid
            if dm_revision_text:
                storyline += "\n\n" + dm_revision_text

            return {
                "dm_response": dm_revision_text
                or "Error in processing the revision response.",
                "full_storyline": storyline,
            }

        else:
            logger.debug(
                f"{Fore.MAGENTA}[NO FEEDBACK] No feedback required from Storyteller. Continuing with the new storyline.{Style.RESET_ALL}"
            )
            storyline += "\n\n" + dm_response_text
            return {"dm_response": dm_response_text, "full_storyline": storyline}

    else:
        logger.debug(
            f"{Fore.MAGENTA}[ONGOING CAMPAIGN] Ongoing campaign detected.{Style.RESET_ALL}"
        )

        if not storyline:
            return {
                "dm_response": "Error continuing the campaign. No storyline found.",
                "full_storyline": "",
            }

        # Create the DM prompt for continuing the campaign
        dm_continue_prompt_content = continue_campaign_prompt(
            context, storyline, user_input
        )
        dm_continue_prompt = [
            {"role": "DMAgent", "content": dm_continue_prompt_content}
        ]

        # Get DM Agent's response
        dm_response = await get_agent_response(
            "DMAgent", dm_continue_prompt, ["dm_response"]
        )
        logger.debug(
            f"{Fore.MAGENTA}[DM RESPONSE] Raw DM Agent response for continuing campaign:\n{Fore.GREEN}{dm_response}{Style.RESET_ALL}"
        )

        if not dm_response:
            return {
                "dm_response": "Error continuing the campaign.",
                "full_storyline": storyline,
            }

        # Extract dm_response
        if isinstance(dm_response, dict):
            dm_response_text = dm_response.get("dm_response", "")
        else:
            logger.error(
                f"{Fore.RED}[ERROR] Could not continue the campaign. Unknown error.{Style.RESET_ALL}"
            )
            return {
                "dm_response": "Error continuing the campaign.",
                "full_storyline": storyline,
            }

        logger.debug(
            f"{Fore.MAGENTA}[STORYLINE] New storyline for ongoing campaign (pending validation):\n{Fore.GREEN}{dm_response_text}{Style.RESET_ALL}"
        )

        # Validate the new storyline using the StorytellerAgent before appending it
        storyteller_continue_prompt_content = validate_storyline_prompt(
            context, dm_response_text
        )
        storyteller_continue_prompt = [
            {"role": "StorytellerAgent", "content": storyteller_continue_prompt_content}
        ]

        storyteller_response = await get_agent_response(
            "StorytellerAgent", storyteller_continue_prompt, ["feedback"]
        )
        logger.debug(
            f"{Fore.MAGENTA}[STORYTELLER RESPONSE] Parsed Storyteller Agent response:\n{Fore.GREEN}{storyteller_response}{Style.RESET_ALL}"
        )

        # Handle Storyteller feedback
        if storyteller_response and isinstance(storyteller_response, dict):
            feedback = storyteller_response.get("feedback", "")

            logger.debug(
                f"{Fore.MAGENTA}[STORYTELLER FEEDBACK] Feedback received: {feedback}{Style.RESET_ALL}"
            )

            # Create a DM revision prompt based on the feedback (whether positive or negative)
            dm_feedback_prompt_content = revise_campaign_prompt(
                context, dm_response_text, feedback
            )
            dm_feedback_prompt = [
                {"role": "DMAgent", "content": dm_feedback_prompt_content}
            ]

            # Get revised response for the storyline based on the feedback
            dm_revision_response = await handle_storyline_feedback(dm_feedback_prompt)

            # Extract revised response
            if isinstance(dm_revision_response, dict):
                dm_revision_text = dm_revision_response.get("dm_response", "")
                if not dm_revision_text:
                    logger.error(
                        f"{Fore.RED}[ERROR] Missing dm_response in the revised response from DMAgent.{Style.RESET_ALL}"
                    )
            else:
                dm_revision_text = ""
                logger.error(
                    f"{Fore.RED}[ERROR] Invalid or missing revised response from DMAgent.{Style.RESET_ALL}"
                )

            logger.debug(
                f"{Fore.MAGENTA}[REVISED STORYLINE] Revised storyline after feedback: {dm_revision_text}{Style.RESET_ALL}"
            )

            # Ensure the revised storyline is appended only if valid
            if dm_revision_text:
                storyline += "\n\n" + dm_revision_text

            return {
                "dm_response": dm_revision_text
                or "Error in processing the revision response.",
                "full_storyline": storyline,
            }

        else:
            logger.debug(
                f"{Fore.MAGENTA}[NO FEEDBACK] No feedback required from Storyteller. Appending the new storyline.{Style.RESET_ALL}"
            )
            storyline += "\n\n" + dm_response_text
            return {"dm_response": dm_response_text, "full_storyline": storyline}
