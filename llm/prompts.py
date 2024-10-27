# llm/prompts.py

def create_campaign_prompt(user_input, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"You are the Dungeon Master of a character-driven, high-fantasy Dungeons & Dragons 5th Edition campaign. "
        f"Design an original, immersive storyline that deeply engages the player’s preferred game style.\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**User Input:**\n{user_input}\n\n"
        f"**Instructions:**\n"
        f"- **Role & Tone:** Act as a narrator, providing descriptions and events in a style that matches the player’s preferred tone (e.g., serious, heroic, whimsical).\n\n"
        f"- **World Building:** Create an intricate, high-fantasy setting filled with mysteries, conflicts, and wonders.\n"
        f"  - Develop a primary quest that introduces challenges aligning with the user's preferences.\n"
        f"  - Include side plots that provide opportunities for exploration, character development, and player agency.\n\n"
        f"- **Immersive Descriptions:** Start with a vivid opening scene, rich with sensory details (sights, sounds, smells) to set the campaign's mood.\n"
        f"  - Describe locations, covering atmosphere, notable landmarks, and any nearby NPCs or creatures.\n"
        f"  - Each scene should allow player-driven decisions without imposing actions or objectives.\n\n"
        f"- **NPCs:**\n"
        f"  - Create NPCs with distinct personalities, motivations, and goals that could reveal secrets, alliances, or conflicts over time.\n"
        f"  - Use unique voices or subtle dialects for significant NPCs to enhance immersion.\n\n"
        f"- **Player Choices:** Present five narrative-aligned actions with clear but open-ended possibilities.\n"
        f"  - One action should be a surprising, risky, or comedic option fitting the scene.\n\n"
        f"- **Response Format:**\n"
        f"  - Provide output in JSON format with the following structure:\n\n"
        f"```json\n"
        f"{{\n"
        f'  "storyline": "<Campaign story overview>",\n'
        f'  "dm_response": "<Detailed scene description>"\n'
        f"}}\n"
        f"```"
    )



def continue_campaign_prompt(context, previous_storyline, user_input, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"You are the Dungeon Master in a detailed, ongoing D&D 5th Edition campaign.\n"
        f"Craft the next scene based on the user’s input and game style preferences without compromising immersion.\n\n"
        f"**User Input:**\n{user_input}\n\n"
        f"**Context:**\n{context}\n\n"
        f"**Previous Storyline:**\n{previous_storyline}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Narrate Responses:** Describe the outcomes of the user’s choices, keeping the tone aligned with the campaign theme (e.g., dark, adventurous, humorous).\n\n"
        f"- **Environment & NPC Interactions:** Expand on settings as the player explores. Describe NPC responses based on personalities, motivations, and context.\n"
        f"  - Introduce hints of NPC backstories if it aligns with the player's actions.\n\n"
        f"- **Present Player Choices:** Offer five options that respect the user’s preferred gameplay and character-driven storytelling style.\n"
        f"  - Include actions that vary in outcome (e.g., cautious, bold, strategic, humorous).\n\n"
        f"- **Response Format:** Provide output in JSON format:\n\n"
        f"```json\n"
        f"{{\n"
        f'  "storyline": "<Optional storyline continuation>",\n'
        f'  "dm_response": "<Narrative response to user input>"\n'
        f"}}\n"
        f"```"
    )


def validate_storyline_prompt(context, storyline, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"Check the campaign storyline against user’s preferences for accuracy, style, and coherence with previous events.\n\n"
        f"**Context:**\n{context}\n\n"
        f"**Storyline:**\n{storyline}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Ensure Alignment:** Confirm storyline maintains consistency with user preferences and previous campaign context.\n"
        f"- **Provide Feedback:** Identify any areas where adjustments might improve alignment with the user's preferences.\n\n"
        f"**Feedback Format:**\n\n"
        f"```json\n"
        f"{{\n"
        f'  "consistency_check": "<Yes/No>",\n'
        f'  "feedback": "<Detailed feedback if needed>"\n'
        f"}}\n"
        f"```"
    )



def revise_campaign_prompt(context, storyline, feedback, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"Revise the storyline to incorporate feedback and ensure alignment with the user's preferences.\n\n"
        f"**Context:**\n{context}\n\n"
        f"**Feedback:**\n{feedback}\n\n"
        f"**Storyline:**\n{storyline}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Adjust Storyline:** Revise any parts noted in the feedback to fit user preferences.\n"
        f"- **Maintain Continuity:** Ensure continuity with previous events and create immersive, consistent gameplay.\n\n"
        f"**Response Format:**\n\n"
        f"```json\n"
        f"{{\n"
        f'  "revised_storyline": "<Updated storyline>",\n'
        f'  "dm_response": "<Narrative response to user after revision>"\n'
        f"}}\n"
        f"```"
    )



def format_feedback_prompt(expected_keys, response):
    return (
        f"Error: The last response had incorrect formatting.\n\n"
        f"Please resend the response in proper JSON format, ensuring all required fields are included.\n"
        f"**Previous Incorrect Response:**\n{response}\n\n"
        f"**Expected JSON Keys:**\n{expected_keys}\n\n"
        f"**Required Format:**\n"
        f"```json\n"
        f"{{\n"
        f'  "key1": "value1",\n'
        f'  "key2": "value2",\n'
        f"}}\n"
        f"```\n\n"
        f"**Corrected Response:**\n"
    )

def feedback_missing_storyline(agent_name):
    return (
        f"Error: The last response from {agent_name} did not include a storyline.\n\n"
        f"Every response must contain a valid storyline, even if only a brief summary or minor narrative details are provided. This is crucial for maintaining campaign flow.\n"
        f"Please resend your response in JSON format, ensuring the 'storyline' field is filled:\n"
        f"```json\n"
        f"{{\n"
        f'  "storyline": "<A brief summary or continuation of the campaign>",\n'
        f'  "dm_response": "<Response to the user>"\n'
        f"}}\n"
        f"```"
    )


def feedback_inconsistent_storyline(agent_name, issue_details):
    return (
        f"The last storyline from {agent_name} contains inconsistencies with the current campaign or user preferences.\n\n"
        f"**Issue Details:**\n{issue_details}\n\n"
        f"Please revise the storyline to resolve these inconsistencies. Ensure that the tone, genre, and progression are consistent with user preferences and that the storyline logically follows previous events.\n"
        f"Resend your response in the following format:\n"
        f"```json\n"
        f"{{\n"
        f'  "revised_storyline": "<Corrected storyline>",\n'
        f'  "dm_response": "<Response to the user>"\n'
        f"}}\n"
        f"```"
    )
