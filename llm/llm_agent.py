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
MAX_RETRIES = 3  # Maximum number of retries for handling inconsistencies

# Import ORM models and database utilities
from sqlalchemy.orm import Session  # noqa: E402
from models.save_game_models import SavedGame, ConversationPair  # noqa: E402


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
                f"{Fore.MAGENTA}[SUCCESS] Parsed JSON from {Fore.BLUE}{agent_name}: "
                f"{Fore.GREEN}{parsed_json}{Style.RESET_ALL}"
            )
            return parsed_json
        else:
            logger.warning(
                f"{Fore.YELLOW}[WARNING] No valid JSON found in response from {Fore.BLUE}{agent_name}. "
                f"Using raw response.{Style.RESET_ALL}"
            )
            return {"raw_response": response}
    except json.JSONDecodeError as e:
        logger.error(
            f"{Fore.RED}[ERROR] Failed to decode JSON from {Fore.BLUE}{agent_name}. Error: {e}{Style.RESET_ALL}"
        )
        return None


async def send_feedback_and_retry(
    agent, agent_name: str, expected_keys: List[str]
) -> Optional[dict]:
    feedback_msg_content = format_feedback_prompt(expected_keys)
    feedback_msg = [{"content": feedback_msg_content, "role": "system"}]

    logger.debug(
        f"{Fore.MAGENTA}[FEEDBACK] Sending feedback to {Fore.BLUE}{agent_name}: "
        f"{Fore.MAGENTA}{feedback_msg}{Style.RESET_ALL}"
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
            f"{Fore.MAGENTA}[FEEDBACK RESPONSE] Raw response from {Fore.BLUE}{agent_name}: "
            f"{Fore.GREEN}{feedback_response}{Style.RESET_ALL}"
        )
        parsed_feedback = await parse_response(agent_name, feedback_response)
        if parsed_feedback and isinstance(parsed_feedback, dict):
            logger.debug(
                f"{Fore.MAGENTA}[PARSED FEEDBACK] Parsed feedback returned: "
                f"{Fore.BLUE}{parsed_feedback}{Style.RESET_ALL}"
            )
            return parsed_feedback
        else:
            logger.error(
                f"{Fore.RED}[ERROR] Invalid feedback format from {Fore.BLUE}{agent_name}. "
                f"Feedback response: {parsed_feedback}{Style.RESET_ALL}"
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
        try:
            logger.debug(
                f"{Fore.MAGENTA}[ATTEMPT {retries + 1}/{max_retries}] Sending prompt to {Fore.BLUE}{agent_name}: "
                f"{Fore.MAGENTA}{msg}{Style.RESET_ALL}"
            )
            response = agent.generate_reply(messages=msg)
            if hasattr(response, "__await__"):
                response = await response
            logger.debug(
                f"{Fore.MAGENTA}[RECEIVED] Raw response from {Fore.BLUE}{agent_name}: "
                f"{Fore.GREEN}{response}{Style.RESET_ALL}"
            )
            parsed_response = await parse_response(agent_name, response)
            if not parsed_response or not isinstance(parsed_response, dict):
                raise ValueError(f"Invalid response format from {agent_name}")
            missing_keys = [key for key in expected_keys if key not in parsed_response]
            if missing_keys:
                raise KeyError(
                    f"Expected key(s) '{missing_keys}' missing in {agent_name}'s response"
                )
            return parsed_response
        except (ValueError, KeyError) as e:
            logger.error(
                f"{Fore.RED}[EXCEPTION] {str(e)} Error handling response from {Fore.BLUE}{agent_name} on attempt "
                f"{retries + 1}.{Style.RESET_ALL}"
            )
        except Exception as e:
            logger.error(
                f"{Fore.RED}[UNEXPECTED EXCEPTION] Error during agent response from {Fore.BLUE}{agent_name}: "
                f"{e}{Style.RESET_ALL}"
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
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    character_details = "\n".join(
        [f"- {key.capitalize()}: {value}" for key, value in current_character.items()]
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
            agent, agent_name, dm_msg, ["dm_response"]
        )
        if revised_response and isinstance(revised_response, dict):
            dm_response_text = revised_response.get("dm_response")
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
        logger.debug("[START] Generating GM response.")

        # Retrieve the saved game
        saved_game = db.query(SavedGame).filter_by(id=saved_game_id).first()
        if not saved_game:
            logger.error(f"Saved game with ID {saved_game_id} not found.")
            return {
                "dm_response": "Error: Unable to find the saved game session. Please start a new game.",
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
        logger.debug(f"[STORYLINE RECONSTRUCTED] Full storyline: {storyline}")

        dm_agent = agents.get("DMAgent")
        if not dm_agent:
            return {
                "dm_response": "Error starting a new campaign.",
                "full_storyline": storyline,
            }

        storyteller_agent = agents.get("StorytellerAgent")
        if not storyteller_agent:
            return {
                "dm_response": "Error validating the storyline.",
                "full_storyline": storyline,
            }

        is_new_campaign = len(conversation_pairs) == 0
        context = build_conversation_context(user_preferences, current_character)

        if is_new_campaign:
            # 1. Generate initial campaign prompt
            dm_prompt_content = create_campaign_prompt(user_input, context)
            dm_msg = [{"content": dm_prompt_content, "role": "user"}]
            dm_response = await get_agent_response(
                dm_agent, "DMAgent", dm_msg, ["dm_response"]
            )
            dm_response_text = (
                dm_response.get("dm_response", "")
                if isinstance(dm_response, dict)
                else ""
            )

            # 2. Validate storyline consistency
            storyteller_prompt_content = validate_storyline_prompt(
                context, dm_response_text
            )
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
                revise_msg = [{"content": revise_prompt_content, "role": "system"}]
                revised_response = await get_agent_response(
                    dm_agent, "DMAgent", revise_msg, ["dm_response"]
                )
                dm_response_text = (
                    revised_response.get("dm_response", "")
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
                    {"content": revise_options_prompt_content, "role": "system"}
                ]
                revised_options_response = await get_agent_response(
                    dm_agent, "DMAgent", revise_options_msg, ["dm_response"]
                )
                dm_response_text = (
                    revised_options_response.get("dm_response", "")
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

            return {"dm_response": dm_response_text, "full_storyline": storyline}

        else:
            # 1. Validate player's action for ongoing campaign
            action_validation_prompt_content = validate_player_action_prompt(
                context, storyline, user_input
            )
            action_validation_msg = [
                {"content": action_validation_prompt_content, "role": "user"}
            ]
            storyteller_agent = agents.get("StorytellerAgent")
            if not storyteller_agent:
                return {
                    "dm_response": "Error validating the player's action.",
                    "full_storyline": storyline,
                }
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
                    context, storyline, user_input, action_feedback
                )
                inform_feedback_msg = [
                    {"content": inform_feedback_prompt_content, "role": "system"}
                ]
                inform_feedback_response = await get_agent_response(
                    dm_agent, "DMAgent", inform_feedback_msg, ["dm_response"]
                )
                dm_response_text = (
                    inform_feedback_response.get("dm_response", "")
                    if isinstance(inform_feedback_response, dict)
                    else ""
                )
                return {"dm_response": dm_response_text, "full_storyline": storyline}

            # 3. Continue campaign
            dm_continue_prompt_content = continue_campaign_prompt(
                context, storyline, user_input
            )
            dm_continue_msg = [{"content": dm_continue_prompt_content, "role": "user"}]
            dm_response = await get_agent_response(
                dm_agent, "DMAgent", dm_continue_msg, ["dm_response"]
            )
            dm_response_text = (
                dm_response.get("dm_response", "")
                if isinstance(dm_response, dict)
                else ""
            )

            # 4. Validate storyline in continuation
            storyline_validation_prompt_content = validate_storyline_prompt(
                context, dm_response_text
            )
            storyline_validation_msg = [
                {"content": storyline_validation_prompt_content, "role": "system"}
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
                    {"content": revise_storyline_prompt_content, "role": "system"}
                ]
                revised_storyline_response = await get_agent_response(
                    dm_agent, "DMAgent", revise_storyline_msg, ["dm_response"]
                )
                dm_response_text = (
                    revised_storyline_response.get("dm_response", "")
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
                    {"content": revise_options_prompt_content, "role": "system"}
                ]
                revised_options_response = await get_agent_response(
                    dm_agent, "DMAgent", revise_options_msg, ["dm_response"]
                )
                dm_response_text = (
                    revised_options_response.get("dm_response", "")
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

            return {"dm_response": dm_response_text, "full_storyline": storyline}
    except Exception as e:
        logger.error(f"[ERROR] Error in GM response generation: {e}")
        logger.error(traceback.format_exc())
        return {"dm_response": "Error generating GM response.", "full_storyline": ""}
