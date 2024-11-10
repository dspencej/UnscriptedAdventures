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
    validate_storyline_prompt,
    validate_options_prompt,
    validate_player_action_prompt,
    revise_storyline_prompt,
    revise_options_prompt,
    inform_invalid_action_prompt,
)
import traceback
import datetime

# SSL Warning Suppression
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logging Configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Constants
MAX_RETRIES = 6

# Import ORM models and database utilities
from sqlalchemy.orm import Session  # noqa: E402
from models.save_game_models import SavedGame, ConversationPair  # noqa: E402


# Helper Functions
async def parse_response(
    agent_name: str, response: str, expected_keys: List[str]
) -> Optional[Dict[str, Any]]:
    logger.info(f"{Fore.GREEN}[PARSING] Response from {agent_name}{Style.RESET_ALL}\n")
    logger.debug(f"{Fore.BLUE}{response}{Style.RESET_ALL}\n")
    try:
        # Attempt to extract and parse JSON
        json_str = extract_json_from_text(response)
        if json_str:
            parsed_json = json.loads(json_str)
            logger.info(
                f"{Fore.GREEN}[SUCCESS] Parsed JSON from {agent_name}{Style.RESET_ALL}\n"
            )
            logger.debug(f"{Fore.BLUE}{parsed_json}{Style.RESET_ALL}\n")

            # Validate expected keys are present
            missing_keys = [key for key in expected_keys if key not in parsed_json]
            if missing_keys:
                logger.warning(
                    f"{Fore.YELLOW}[WARNING] Missing expected keys in JSON from {agent_name}. "
                    f"Expected keys: {expected_keys}, Missing keys: {missing_keys}{Style.RESET_ALL}"
                )
                return None
            return parsed_json
        else:
            logger.warning(
                f"{Fore.YELLOW}[WARNING] No valid JSON found in response from {agent_name}. "
            )
            return None
    except json.JSONDecodeError as e:
        # Log error and set return to None to trigger feedback
        logger.error(
            f"{Fore.RED}[ERROR] Failed to decode JSON from {Fore.BLUE}{agent_name}. Error: {e}{Style.RESET_ALL}"
        )
        return None


async def send_feedback(
    agent, agent_name: str, expected_keys: List[str], previous_response: str
) -> Optional[dict]:
    feedback_msg_content = format_feedback_prompt(expected_keys, previous_response)
    feedback_msg = [{"content": feedback_msg_content, "role": "user"}]
    logger.info(
        f"{Fore.GREEN}[SENDING FEEDBACK] Sending feedback to {agent_name}{Style.RESET_ALL}\n"
    )
    logger.debug(f"{Fore.BLUE}{feedback_msg}{Style.RESET_ALL}{Style.RESET_ALL}\n")

    if not agent:
        logger.error(
            f"{Fore.RED}[ERROR] Agent '{agent_name}' not provided.{Style.RESET_ALL}"
        )
        return None

    try:
        feedback_response = agent.generate_reply(messages=feedback_msg)
        if hasattr(feedback_response, "__await__"):
            feedback_response = await feedback_response
        logger.info(
            f"{Fore.GREEN}[FEEDBACK RESPONSE] Raw response from {agent_name}{Style.RESET_ALL}\n"
        )
        logger.debug(f"{Fore.BLUE}{feedback_response}{Style.RESET_ALL}\n")
        return feedback_response

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
        try:
            attempt_number = retries + 1
            logger.info(
                f"{Fore.GREEN}[ATTEMPT {attempt_number}/{max_retries}] Sending message to {Fore.BLUE}{agent_name}{Style.RESET_ALL}\n"
            )
            logger.debug(f"{Fore.BLUE}{msg}{Style.RESET_ALL}\n")

            response = agent.generate_reply(messages=msg)
            if hasattr(response, "__await__"):
                response = await response
            logger.info(
                f"{Fore.GREEN}[RECEIVED] Raw response from {agent_name}{Style.RESET_ALL}\n"
            )
            logger.debug(f"{Fore.BLUE}{response}{Style.RESET_ALL}\n")
            parsed_response = await parse_response(agent_name, response, expected_keys)

            # If parsing fails or keys are missing, send feedback and retry
            if not parsed_response or any(
                key not in parsed_response for key in expected_keys
            ):
                logger.warning(
                    f"{Fore.YELLOW}[REQUESTING FEEDBACK] Response from {agent_name}{Style.RESET_ALL}\n"
                )

                feedback_response = await send_feedback(
                    agent, agent_name, expected_keys, response
                )

                parsed_response = await parse_response(
                    agent_name, feedback_response, expected_keys
                )

                # Check if feedback response has the required keys
                if parsed_response and all(
                    key in parsed_response for key in expected_keys
                ):
                    return parsed_response  # Return if feedback response is valid
                else:
                    retries += 1  # Retry if feedback did not resolve the issue
                    continue

            return parsed_response

        except Exception as e:
            logger.error(
                f"{Fore.RED}[UNEXPECTED EXCEPTION] Error during agent response from {agent_name}: "
                f"{e}{Style.RESET_ALL}"
            )
            logger.error(traceback.format_exc())

        retries += 1

    logger.warning(f"{Fore.RED}[FINAL FAILURE] All retries exhausted.{Style.RESET_ALL}")
    return {"response": ""}


def extract_json_from_text(response: str) -> Optional[str]:
    # Pattern to capture JSON blocks enclosed in backticks
    json_block_pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(json_block_pattern, response, re.DOTALL)
    if match:
        json_str = match.group(1)
        # Remove control characters without affecting the JSON formatting
        json_str = re.sub(r"[\x00-\x1F\x7F]", "", json_str)
        return json_str

    # Fallback pattern to capture JSON-like structures even without backticks
    json_pattern = r"(\{.*?\})"
    match = re.search(json_pattern, response, re.DOTALL)
    if match:
        json_str = match.group(1)
        json_str = re.sub(r"[\x00-\x1F\x7F]", "", json_str)
        return json_str

    # Log an error if JSON extraction fails
    logger.error(
        f"{Fore.RED}[ERROR] No valid JSON block found in the response.{Style.RESET_ALL}"
    )
    return None


def build_conversation_context(
    user_preferences: Dict[str, str],
    current_character: Dict[str, Any],
) -> str:
    # Define fields to exclude from the character details
    excluded_fields = {
        "id",
        "experience_points",
        "max_hit_points",
        "current_hit_points",
    }

    # Build preferences text
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )

    # Filter out excluded fields and build character details text
    character_details = "\n".join(
        [
            f"- {key.capitalize()}: {value}"
            for key, value in current_character.items()
            if key.lower() not in excluded_fields
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
            agent, agent_name, dm_msg, ["response"]
        )
        if revised_response and isinstance(revised_response, dict):
            dm_response_text = revised_response.get("response")
            if dm_response_text:
                return revised_response
        retries += 1
    return None


# Main Function
async def generate_gm_response(
    user_input: str,
    user_preferences: Dict[str, str],
    current_character: Dict[str, Any],
    agents: Dict[str, Any],
    saved_game_id: int,
    db: Session,
) -> Dict[str, str]:
    try:
        logger.debug(f"{Fore.MAGENTA}[START] Generating GM response.{Style.RESET_ALL}")
        # Retrieve the saved game
        saved_game = db.query(SavedGame).filter_by(id=saved_game_id).first()
        if not saved_game:
            logger.error(f"Saved game with ID {saved_game_id} not found.")
            return {
                "response": "Error: Unable to find the saved game session. Please start a new game.",
                "full_storyline": "",
            }

        # Retrieve conversation pairs ordered by 'order'
        conversation_pairs = (
            db.query(ConversationPair)
            .filter_by(game_id=saved_game_id)
            .order_by(ConversationPair.order)
            .all()
        )

        # Reconstruct the storyline
        storyline = "\n".join(
            [
                f"User: {pair.user_input}\nGM: {pair.gm_response}"
                for pair in conversation_pairs
            ]
        )
        logger.info(
            f"{Fore.GREEN}[RECONSTRUCTING STORYLINE] {Style.RESET_ALL}\n"
        )
        logger.debug(
            f"{Fore.BLUE}Full storyline: {storyline}{Style.RESET_ALL}\n"
        )

        dm_agent = agents.get("DMAgent")
        if not dm_agent:
            return {
                "response": "Error starting a new campaign.",
                "full_storyline": storyline,
            }

        storyteller_agent = agents.get("StorytellerAgent")
        if not storyteller_agent:
            return {
                "response": "Error validating the storyline.",
                "full_storyline": storyline,
            }

        is_new_campaign = len(conversation_pairs) == 0
        context = build_conversation_context(user_preferences, current_character)

        if is_new_campaign:
            # 1. Generate initial campaign prompt
            dm_prompt_content = create_campaign_prompt(user_input, context)
            dm_msg = [{"content": dm_prompt_content, "role": "user"}]
            dm_response = await get_agent_response(
                dm_agent, "DMAgent", dm_msg, ["response"]
            )
            dm_response_text = (
                dm_response.get("response", "") if isinstance(dm_response, dict) else ""
            )

            # 2. Validate storyline consistency
            storyteller_prompt_content = validate_storyline_prompt(context, storyline)
            storyteller_msg = [{"content": storyteller_prompt_content, "role": "user"}]
            storyteller_response = await get_agent_response(
                storyteller_agent, "StorytellerAgent", storyteller_msg, ["feedback"]
            )
            feedback = (
                storyteller_response.get("feedback", "")
                if isinstance(storyteller_response, dict)
                else ""
            )

            # 3. Revise storyline based on feedback if needed
            if feedback:
                revise_prompt_content = revise_storyline_prompt(
                    context, dm_response_text, feedback
                )
                revise_msg = [{"content": revise_prompt_content, "role": "user"}]
                revised_response = await get_agent_response(
                    dm_agent, "DMAgent", revise_msg, ["response"]
                )
                dm_response_text = (
                    revised_response.get("response", "")
                    if isinstance(revised_response, dict)
                    else ""
                )

            # 4. Validate options in DM response
            options_validation_prompt_content = validate_options_prompt(
                context, dm_response_text
            )
            options_validation_msg = [
                {"content": options_validation_prompt_content, "role": "user"}
            ]
            options_feedback_response = await get_agent_response(
                storyteller_agent,
                "StorytellerAgent",
                options_validation_msg,
                ["feedback"],
            )
            options_feedback = (
                options_feedback_response.get("feedback", "")
                if isinstance(options_feedback_response, dict)
                else ""
            )

            # 5. Revise options based on feedback if needed
            if options_feedback:
                revise_options_prompt_content = revise_options_prompt(
                    context, dm_response_text, options_feedback
                )
                revise_options_msg = [
                    {"content": revise_options_prompt_content, "role": "user"}
                ]
                revised_options_response = await get_agent_response(
                    dm_agent, "DMAgent", revise_options_msg, ["response"]
                )
                dm_response_text = (
                    revised_options_response.get("response", "")
                    if isinstance(revised_options_response, dict)
                    else ""
                )

            # Save the new conversation pair to the database
            new_conversation_pair = ConversationPair(
                game_id=saved_game_id,
                order=1,
                user_input=user_input,
                gm_response=dm_response_text,
                timestamp=datetime.datetime.now(datetime.UTC),
            )
            db.add(new_conversation_pair)
            db.commit()

            return {"response": dm_response_text, "full_storyline": storyline}

        else:
            # 1. Validate player's action for ongoing campaign
            action_validation_prompt_content = validate_player_action_prompt(
                context, storyline, user_input
            )
            action_validation_msg = [
                {"content": action_validation_prompt_content, "role": "user"}
            ]

            action_feedback_response = await get_agent_response(
                storyteller_agent,
                "StorytellerAgent",
                action_validation_msg,
                ["feedback"],
            )
            action_feedback = (
                action_feedback_response.get("feedback", "")
                if isinstance(action_feedback_response, dict)
                else ""
            )

            if action_feedback:
                # 2. Inform the player if action is invalid
                inform_feedback_prompt_content = inform_invalid_action_prompt(
                    context, storyline, user_input
                )
                inform_feedback_msg = [
                    {"content": inform_feedback_prompt_content, "role": "user"}
                ]
                inform_feedback_response = await get_agent_response(
                    dm_agent, "DMAgent", inform_feedback_msg, ["response"]
                )
                dm_response_text = (
                    inform_feedback_response.get("response", "")
                    if isinstance(inform_feedback_response, dict)
                    else ""
                )
                return {"response": dm_response_text, "full_storyline": storyline}

            # 3. Continue campaign
            dm_continue_prompt_content = continue_campaign_prompt(
                context, storyline, user_input
            )
            dm_continue_msg = [{"content": dm_continue_prompt_content, "role": "user"}]
            dm_response = await get_agent_response(
                dm_agent, "DMAgent", dm_continue_msg, ["response"]
            )
            dm_response_text = (
                dm_response.get("response", "") if isinstance(dm_response, dict) else ""
            )

            # 4. Validate storyline in continuation
            storyline_validation_prompt_content = validate_storyline_prompt(
                context, dm_response_text
            )
            storyline_validation_msg = [
                {"content": storyline_validation_prompt_content, "role": "user"}
            ]
            storyline_feedback_response = await get_agent_response(
                storyteller_agent,
                "StorytellerAgent",
                storyline_validation_msg,
                ["feedback"],
            )
            storyline_feedback = (
                storyline_feedback_response.get("feedback", "")
                if isinstance(storyline_feedback_response, dict)
                else ""
            )

            # 5. Revise storyline based on feedback if needed
            if storyline_feedback:
                revise_storyline_prompt_content = revise_storyline_prompt(
                    context, dm_response_text, storyline_feedback
                )
                revise_storyline_msg = [
                    {"content": revise_storyline_prompt_content, "role": "user"}
                ]
                revised_storyline_response = await get_agent_response(
                    dm_agent, "DMAgent", revise_storyline_msg, ["response"]
                )
                dm_response_text = (
                    revised_storyline_response.get("response", "")
                    if isinstance(revised_storyline_response, dict)
                    else ""
                )

            # 6. Validate options in DM response for continuation
            options_validation_prompt_content = validate_options_prompt(
                context, dm_response_text
            )
            options_validation_msg = [
                {"content": options_validation_prompt_content, "role": "user"}
            ]
            options_feedback_response = await get_agent_response(
                storyteller_agent,
                "StorytellerAgent",
                options_validation_msg,
                ["feedback"],
            )
            options_feedback = (
                options_feedback_response.get("feedback", "")
                if isinstance(options_feedback_response, dict)
                else ""
            )

            # 7. Revise options based on feedback if needed
            if options_feedback:
                revise_options_prompt_content = revise_options_prompt(
                    context, dm_response_text, options_feedback
                )
                revise_options_msg = [
                    {"content": revise_options_prompt_content, "role": "user"}
                ]
                revised_options_response = await get_agent_response(
                    dm_agent, "DMAgent", revise_options_msg, ["response"]
                )
                dm_response_text = (
                    revised_options_response.get("response", "")
                    if isinstance(revised_options_response, dict)
                    else ""
                )

            # Save the new conversation pair to the database
            new_order = len(conversation_pairs) + 1
            new_conversation_pair = ConversationPair(
                game_id=saved_game_id,
                order=new_order,
                user_input=user_input,
                gm_response=dm_response_text,
                timestamp=datetime.datetime.now(datetime.UTC),
            )
            db.add(new_conversation_pair)
            db.commit()

            return {"response": dm_response_text, "full_storyline": storyline}
    except Exception as e:
        logger.error(f"[ERROR] Error in GM response generation: {e}")
        logger.error(traceback.format_exc())
        return {"response": "Error generating GM response.", "full_storyline": ""}
