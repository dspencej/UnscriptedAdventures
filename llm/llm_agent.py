# llm/llm_agent.py

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union
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

DMAgent = "DMAgent"
StorytellerAgent = "StorytellerAgent"


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
) -> Optional[Union[dict, str]]:
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
                f"{Fore.GREEN}[ATTEMPT {attempt_number}/{max_retries}] Sending message to {agent_name}{Style.RESET_ALL}\n"
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
                    f"{Fore.YELLOW}[REQUESTING FEEDBACK] Missing keys or invalid format from {agent_name}{Style.RESET_ALL}\n"
                )

                feedback_response = await send_feedback(
                    agent, agent_name, expected_keys, response
                )

                parsed_response = await parse_response(
                    agent_name, feedback_response, expected_keys
                )

                # Log each feedback attempt to confirm retry mechanism
                logger.debug(
                    f"{Fore.YELLOW}[FEEDBACK RETRY] Feedback attempt {attempt_number}/{max_retries} - Parsed response: {parsed_response}{Style.RESET_ALL}"
                )

                # If feedback response has the required keys, return it
                if parsed_response and all(
                    key in parsed_response for key in expected_keys
                ):
                    return parsed_response
                else:
                    # Retry if feedback did not resolve the issue
                    retries += 1
                    continue

            # Valid parsed response, return it
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

    # Filter out excluded fields and build core character details text
    character_core_details = "\n".join(
        [
            f"- {key.capitalize()}: {value}"
            for key, value in current_character.items()
            if key.lower() not in excluded_fields
        ]
    )

    # Add alignment if available
    alignment = current_character.get("alignment", "Unknown")

    # Ensure background is a dictionary; handle case where it's a string or missing
    background = current_character.get("background", {})
    if isinstance(background, str):
        background_text = f"Background: {background}"
    else:
        background_text = (
            f"Name: {background.get('name', 'Unknown')}\n"
            f"Feature: {background.get('feature', 'None')}\n"
            f"Personality Traits: {', '.join(background.get('personality_traits', []))}\n"
            f"Ideals: {', '.join(background.get('ideals', []))}\n"
            f"Bonds: {', '.join(background.get('bonds', []))}\n"
            f"Flaws: {', '.join(background.get('flaws', []))}"
        )

    # Add skills and proficiencies if available
    skills = current_character.get("skills", [])
    skills_text = (
        "\n".join([f"  - {skill.name} ({skill.ability})" for skill in skills])
        if skills
        else "None"
    )

    proficiencies = current_character.get("proficiencies", [])
    proficiencies_text = (
        "\n".join([f"  - {prof.name} ({prof.type})" for prof in proficiencies])
        if proficiencies
        else "None"
    )

    # Add languages if available
    languages = current_character.get("languages", [])
    languages_text = (
        ", ".join([language.name for language in languages]) if languages else "None"
    )

    # Add feats if available
    feats = current_character.get("feats", [])
    feats_text = (
        "\n".join([f"  - {feat.name}: {feat.description}" for feat in feats])
        if feats
        else "None"
    )

    # Add features if available
    features = current_character.get("features", [])
    features_text = (
        "\n".join(
            [f"  - {feature.name}: {feature.description}" for feature in features]
        )
        if features
        else "None"
    )

    return f"""User Preferences:
{preferences_text}

Character Core Details:
{character_core_details}

Alignment:
{alignment}

Background:
{background_text}

Skills:
{skills_text}

Proficiencies:
{proficiencies_text}

Languages:
{languages_text}

Feats:
{feats_text}

Features:
{features_text}
"""


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


# Helper function to generate initial DM response and handle feedback
async def generate_initial_campaign_response(user_input, context, dm_agent):
    dm_prompt_content = create_campaign_prompt(user_input, context)
    dm_msg = [{"content": dm_prompt_content, "role": "user"}]
    dm_response = await get_agent_response(dm_agent, DMAgent, dm_msg, ["response"])
    return dm_response.get("response", "") if isinstance(dm_response, dict) else ""


# Helper function for continuing an existing campaign
async def continue_campaign_response(user_input, context, storyline, dm_agent):
    dm_continue_prompt_content = continue_campaign_prompt(
        context, storyline, user_input
    )
    dm_continue_msg = [{"content": dm_continue_prompt_content, "role": "user"}]
    dm_response = await get_agent_response(
        dm_agent, DMAgent, dm_continue_msg, ["response"]
    )
    return dm_response.get("response", "") if isinstance(dm_response, dict) else ""


# Helper function to validate and revise storyline
async def validate_and_revise_storyline(
    context, storyline, dm_response_text, storyteller_agent, dm_agent
):
    prompt_content = validate_storyline_prompt(context, storyline)
    msg = [{"content": prompt_content, "role": "user"}]
    feedback_response = await get_agent_response(
        storyteller_agent, StorytellerAgent, msg, ["feedback"]
    )
    feedback = (
        feedback_response.get("feedback", "")
        if isinstance(feedback_response, dict)
        else ""
    )

    if feedback:
        revise_prompt_content = revise_storyline_prompt(
            context, dm_response_text, feedback
        )
        revise_msg = [{"content": revise_prompt_content, "role": "user"}]
        revised_response = await get_agent_response(
            dm_agent, DMAgent, revise_msg, ["response"]
        )
        return (
            revised_response.get("response", "")
            if isinstance(revised_response, dict)
            else dm_response_text
        )

    return dm_response_text


# Helper function to validate and revise options
async def validate_and_revise_options(
    context, dm_response_text, storyteller_agent, dm_agent
):
    options_prompt_content = validate_options_prompt(context, dm_response_text)
    options_msg = [{"content": options_prompt_content, "role": "user"}]
    options_feedback_response = await get_agent_response(
        storyteller_agent, StorytellerAgent, options_msg, ["feedback"]
    )
    options_feedback = (
        options_feedback_response.get("feedback", "")
        if isinstance(options_feedback_response, dict)
        else ""
    )

    if options_feedback:
        revise_options_prompt_content = revise_options_prompt(
            context, dm_response_text, options_feedback
        )
        revise_options_msg = [
            {"content": revise_options_prompt_content, "role": "user"}
        ]
        revised_options_response = await get_agent_response(
            dm_agent, DMAgent, revise_options_msg, ["response"]
        )
        return (
            revised_options_response.get("response", "")
            if isinstance(revised_options_response, dict)
            else dm_response_text
        )

    return dm_response_text


# Helper function to save conversation pair to database
def save_conversation_pair(db, saved_game_id, order, user_input, gm_response_text):
    new_conversation_pair = ConversationPair(
        game_id=saved_game_id,
        order=order,
        user_input=user_input,
        gm_response=gm_response_text,
        timestamp=datetime.datetime.now(datetime.UTC),
    )
    db.add(new_conversation_pair)
    db.commit()


def get_storyline(db, saved_game_id):
    conversation_pairs = (
        db.query(ConversationPair)
        .filter_by(game_id=saved_game_id)
        .order_by(ConversationPair.order)
        .all()
    )
    storyline = "\n".join(
        [
            f"User: {pair.user_input}\nGM: {pair.gm_response}"
            for pair in conversation_pairs
        ]
    )
    return storyline, conversation_pairs


async def handle_invalid_action(
    context, storyline, user_input, storyteller_agent, dm_agent
):
    action_validation_prompt_content = validate_player_action_prompt(
        context, storyline, user_input
    )
    action_validation_msg = [
        {"content": action_validation_prompt_content, "role": "user"}
    ]
    action_feedback_response = await get_agent_response(
        storyteller_agent, StorytellerAgent, action_validation_msg, ["feedback"]
    )
    action_feedback = (
        action_feedback_response.get("feedback", "")
        if isinstance(action_feedback_response, dict)
        else ""
    )

    if action_feedback:
        inform_feedback_prompt_content = inform_invalid_action_prompt(
            context, storyline, user_input
        )
        inform_feedback_msg = [
            {"content": inform_feedback_prompt_content, "role": "user"}
        ]
        inform_feedback_response = await get_agent_response(
            dm_agent, DMAgent, inform_feedback_msg, ["response"]
        )
        return (
            inform_feedback_response.get("response", "")
            if isinstance(inform_feedback_response, dict)
            else ""
        )
    return None  # No invalid action detected


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

        saved_game = db.query(SavedGame).filter_by(id=saved_game_id).first()
        if not saved_game:
            logger.error(f"Saved game with ID {saved_game_id} not found.")
            return {
                "response": "Error: Unable to find the saved game session. Please start a new game."
            }

        # Retrieve storyline and context
        storyline, conversation_pairs = get_storyline(db, saved_game_id)
        context = build_conversation_context(user_preferences, current_character)
        is_new_campaign = len(conversation_pairs) == 0

        dm_agent = agents.get(DMAgent)
        storyteller_agent = agents.get(StorytellerAgent)
        if not dm_agent or not storyteller_agent:
            return {
                "response": "Error: Missing agents for campaign response generation."
            }

        if is_new_campaign:
            dm_response_text = await generate_initial_campaign_response(
                user_input, context, dm_agent
            )
            dm_response_text = await validate_and_revise_storyline(
                context, storyline, dm_response_text, storyteller_agent, dm_agent
            )
            dm_response_text = await validate_and_revise_options(
                context, dm_response_text, storyteller_agent, dm_agent
            )
            save_conversation_pair(db, saved_game_id, 1, user_input, dm_response_text)
            return {"response": dm_response_text}  # Only GM response text

        else:
            # Validate action and handle invalid actions if necessary
            invalid_action_response = await handle_invalid_action(
                context, storyline, user_input, storyteller_agent, dm_agent
            )
            if invalid_action_response:
                return {"response": invalid_action_response}

            dm_response_text = await continue_campaign_response(
                user_input, context, storyline, dm_agent
            )
            dm_response_text = await validate_and_revise_storyline(
                context, dm_response_text, storyline, storyteller_agent, dm_agent
            )
            dm_response_text = await validate_and_revise_options(
                context, dm_response_text, storyteller_agent, dm_agent
            )

            new_order = len(conversation_pairs) + 1
            save_conversation_pair(
                db, saved_game_id, new_order, user_input, dm_response_text
            )
            return {"response": dm_response_text}  # Only GM response text

    except Exception as e:
        logger.error(f"[ERROR] Error in GM response generation: {e}")
        logger.error(traceback.format_exc())
        return {"response": "Error generating GM response."}
