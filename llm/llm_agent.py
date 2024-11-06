# llm/llm_agent.py

import json
import logging
import re
from typing import Any, Dict, List, Optional
import urllib3
from colorama import Fore, Style
from llm.prompts import (
    continue_campaign_prompt,
    create_campaign_prompt,
    format_feedback_prompt,
    revise_campaign_prompt,
    validate_storyline_prompt,
)
import traceback

# SSL Warning Suppression
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logging Configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Constants
MAX_RETRIES = 3  # Maximum number of retries for handling inconsistencies

# Helper Functions
async def parse_response(agent_name: str, response: str) -> Optional[Dict[str, Any]]:
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
        agent,
        agent_name: str,
        expected_keys: List[str]
) -> Optional[dict]:
    feedback_msg_content = format_feedback_prompt(expected_keys)
    feedback_msg = [{"content": feedback_msg_content, "role": "system"}]

    logger.debug(
        f"{Fore.MAGENTA}[FEEDBACK] Sending feedback to {Fore.BLUE}{agent_name}: {Fore.MAGENTA}{feedback_msg}{Style.RESET_ALL}"
    )

    if not agent:
        logger.error(
            f"{Fore.RED}[ERROR] Agent '{agent_name}' not provided.{Style.RESET_ALL}"
        )
        return None

    try:
        feedback_response = agent.generate_reply(messages=feedback_msg)
        if hasattr(feedback_response, "__await__"):
            feedback_response = await feedback_response
        logger.debug(
            f"{Fore.MAGENTA}[FEEDBACK RESPONSE] Raw response from {Fore.BLUE}{agent_name}: {Fore.GREEN}{feedback_response}{Style.RESET_ALL}"
        )
        parsed_feedback = await parse_response(agent_name, feedback_response)
        if parsed_feedback and isinstance(parsed_feedback, dict):
            logger.debug(
                f"{Fore.MAGENTA}[PARSED FEEDBACK] Parsed feedback returned: {Fore.BLUE}{parsed_feedback}{Style.RESET_ALL}"
            )
            return parsed_feedback
        else:
            logger.error(
                f"{Fore.RED}[ERROR] Invalid feedback format from {Fore.BLUE}{agent_name}. Feedback response: {parsed_feedback}{Style.RESET_ALL}"
            )
            return None
    except Exception as e:
        logger.error(
            f"{Fore.RED}[UNEXPECTED EXCEPTION] Error during feedback and retry with {agent_name}: {e}{Style.RESET_ALL}"
        )
        logger.error(traceback.format_exc())
        return None

async def get_agent_response(
        agent,
        agent_name: str,
        msg: List[Dict[str, str]],
        expected_keys: List[str],
        max_retries: int = MAX_RETRIES,
) -> Optional[dict]:
    if not agent:
        logger.error(
            f"{Fore.RED}[ERROR] Agent '{agent_name}' not provided.{Style.RESET_ALL}"
        )
        return None

    retries = 0
    while retries < max_retries:
        response = ""
        try:
            logger.debug(
                f"{Fore.MAGENTA}[ATTEMPT {retries + 1}/{max_retries}] Sending prompt to {Fore.BLUE}{agent_name}: {Fore.MAGENTA}{msg}{Style.RESET_ALL}"
            )
            response = agent.generate_reply(messages=msg)
            if hasattr(response, "__await__"):
                response = await response
            logger.debug(
                f"{Fore.MAGENTA}[RECEIVED] Raw response from {Fore.BLUE}{agent_name}: {Fore.GREEN}{response}{Style.RESET_ALL}"
            )
            parsed_response = await parse_response(agent_name, response)
            if not parsed_response or not isinstance(parsed_response, dict):
                raise ValueError(f"Invalid response format from {agent_name}")
            missing_keys = [key for key in expected_keys if key not in parsed_response]
            if missing_keys:
                raise KeyError(f"Expected key(s) '{missing_keys}' missing in {agent_name}'s response")
            return parsed_response
        except (ValueError, KeyError) as e:
            logger.error(
                f"{Fore.RED}[EXCEPTION] {str(e)} Error handling response from {Fore.BLUE}{agent_name} on attempt {retries + 1}.{Style.RESET_ALL}"
            )
        except Exception as e:
            logger.error(
                f"{Fore.RED}[UNEXPECTED EXCEPTION] Error during agent response from {Fore.BLUE}{agent_name}: {e}{Style.RESET_ALL}"
            )
            logger.error(traceback.format_exc())
        retries += 1
        logger.debug(
            f"{Fore.MAGENTA}[RETRY] Sending feedback and attempting retry process.{Style.RESET_ALL}"
        )
        extracted = await send_feedback_and_retry(agent, agent_name, expected_keys)
        if extracted:
            return extracted
        else:
            logger.warning(
                f"{Fore.YELLOW}[RETRY FAILED] Attempt {retries}/{max_retries} failed.{Style.RESET_ALL}"
            )
    return None

def extract_json_from_text(response: str) -> Optional[str]:
    json_block_pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(json_block_pattern, response, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return re.sub(r"[\x00-\x1F\x7F]", "", json_str)
        except Exception as e:
            logger.error(
                f"{Fore.RED}[ERROR] Cleaning JSON block failed: {e}{Style.RESET_ALL}"
            )
            return None
    json_pattern = r"(\{.*?\})"
    match = re.search(json_pattern, response, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return re.sub(r"[\x00-\x1F\x7F]", "", json_str)
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
        user_preferences: Dict[str, str],
        current_character: Dict[str, Any],
) -> str:
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    character_details = "\n".join(
        [
            f"- {key.capitalize()}: {value}"
            for key, value in current_character.items()
        ]
    )
    return f"User Preferences:\n{preferences_text}\n\nCharacter Details:\n{character_details}\n"

async def handle_storyline_feedback(
        dm_msg: List[Dict[str, str]], agent, agent_name: str, max_retries: int = MAX_RETRIES
) -> Optional[Dict[str, Any]]:
    retries = 0
    while retries < max_retries:
        logger.debug(
            f"{Fore.MAGENTA}[ATTEMPT {retries + 1}/{max_retries}] Handling storyline feedback.{Style.RESET_ALL}"
        )
        revised_response = await get_agent_response(
            agent,
            agent_name,
            dm_msg,
            ["dm_response"]
        )
        if revised_response and isinstance(revised_response, dict):
            dm_response_text = (
                    revised_response.get("dm_response")
            )
            if dm_response_text:
                return revised_response
        retries += 1
    return None

# Main Function
async def generate_gm_response(
        user_input: str,
        conversation_history: List[Dict[str, str]],
        user_preferences: Dict[str, str],
        storyline: str,
        current_character: Dict[str, Any],
        agents: Dict[str, Any],
) -> Dict[str, str]:
    try:
        logger.debug(
            f"{Fore.MAGENTA}[START] Generating GM response.{Style.RESET_ALL}"
        )
        # Reconstruct the storyline from the conversation history
        storyline = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history])
        logger.debug(
            f"{Fore.MAGENTA}[STORYLINE RECONSTRUCTED] Full storyline:\n{Fore.GREEN}{storyline}{Style.RESET_ALL}"
        )

        is_new_campaign = not conversation_history or len(conversation_history) == 0
        context = build_conversation_context(user_preferences, current_character)

        if is_new_campaign:
            dm_prompt_content = create_campaign_prompt(user_input, context)
            dm_msg = [{"content": dm_prompt_content, "role": "user"}]
            dm_agent = agents.get("DMAgent")
            if not dm_agent:
                return {"dm_response": "Error starting a new campaign.", "full_storyline": storyline}
            dm_response = await get_agent_response(dm_agent, "DMAgent", dm_msg, ["dm_response"])
            if not dm_response:
                return {"dm_response": "Error starting a new campaign.", "full_storyline": storyline}
            dm_response_text = dm_response.get("dm_response", "") if isinstance(dm_response, dict) else ""
            storyline += f"\n\nUser: {user_input}\nDM: {dm_response_text}"
            storyteller_agent = agents.get("StorytellerAgent")
            if not storyteller_agent:
                return {"dm_response": "Error validating the storyline.", "full_storyline": storyline}
            storyteller_prompt_content = validate_storyline_prompt(context, dm_response_text)
            storyteller_msg = [{"content": storyteller_prompt_content, "role": "user"}]
            storyteller_response = await get_agent_response(storyteller_agent, "StorytellerAgent", storyteller_msg, ["feedback"])
            feedback = storyteller_response.get("feedback", "") if isinstance(storyteller_response, dict) else ""
            if feedback:
                dm_feedback_prompt_content = revise_campaign_prompt(context, dm_response_text, feedback)
                dm_feedback_msg = [{"content": dm_feedback_prompt_content, "role": "system"}]
                dm_revision_response = await handle_storyline_feedback(dm_feedback_msg, agents.get("DMAgent"), "DMAgent")
                dm_revision_text = dm_revision_response.get("dm_response", "") if isinstance(dm_revision_response, dict) else ""
                if dm_revision_text:
                    storyline += f"\nDM (revised): {dm_revision_text}"
                    return {"dm_response": dm_revision_text, "full_storyline": storyline}
            return {"dm_response": dm_response_text, "full_storyline": storyline}
        else:

            dm_continue_prompt_content = continue_campaign_prompt(context, storyline, user_input)
            dm_continue_msg = [{"content": dm_continue_prompt_content, "role": "user"}]
            dm_agent = agents.get("DMAgent")
            if not dm_agent:
                return {"dm_response": "Error continuing the campaign.", "full_storyline": storyline}
            dm_response = await get_agent_response(dm_agent, "DMAgent", dm_continue_msg, ["dm_response"])
            dm_response_text = dm_response.get("dm_response", "") if isinstance(dm_response, dict) else ""

            storyteller_agent = agents.get("StorytellerAgent")
            if not storyteller_agent:
                return {"dm_response": "Error validating the storyline.", "full_storyline": storyline}
            storyteller_continue_prompt_content = validate_storyline_prompt(context, dm_response_text)
            storyteller_continue_msg = [{"content": storyteller_continue_prompt_content, "role": "system"}]
            storyteller_response = await get_agent_response(storyteller_agent, "StorytellerAgent", storyteller_continue_msg, ["feedback"])
            feedback = storyteller_response.get("feedback", "") if isinstance(storyteller_response, dict) else ""
            if feedback:
                dm_feedback_prompt_content = revise_campaign_prompt(context, dm_response_text, feedback)
                dm_feedback_msg = [{"content": dm_feedback_prompt_content, "role": "system"}]
                dm_revision_response = await handle_storyline_feedback(dm_feedback_msg, agents.get("DMAgent"), "DMAgent")
                dm_revision_text = dm_revision_response.get("dm_response", "") if isinstance(dm_revision_response, dict) else ""
                if dm_revision_text:
                    storyline += f"\nDM (revised): {dm_revision_text}"
                    return {"dm_response": dm_revision_text, "full_storyline": storyline}
            return {"dm_response": dm_response_text, "full_storyline": storyline}
    except Exception as e:
        logger.error(f"{Fore.RED}[ERROR] Error in GM response generation: {e}{Style.RESET_ALL}")
        return {"dm_response": "Error generating GM response.", "full_storyline": storyline}
