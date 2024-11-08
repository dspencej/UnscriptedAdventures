# llm/prompts.py

def create_campaign_prompt(user_input, context):
    return (
        f"You are the Dungeon Master (DM) for a Dungeons & Dragons 5th Edition campaign. You have one player in your campaign."
        f"Create a rich storyline based on the player's game preferences.\n"
        f"**Player Preferences and Character Details:**\n{context}\n\n"
        f"Respond to the player's input in your response.\n"
        f"**Player Input:**\n{user_input}\n\n"
        f"**Instructions:**\n"
        f"- Begin with a **scene description**, followed by an interaction type (e.g., dialogue choices, skill check, free exploration).\n"
        f"- Alternate between different styles of engagement, sometimes offering open-ended actions, sometimes focusing on dialogue or skill challenges.\n"
        f"- Keep descriptions vivid, add sensory details, and create an enticing atmosphere.\n"
        f"- Introduce **narrative hooks or mysteries** that encourage exploration and curiosity.\n"
        f"- Occasionally reference past actions to create continuity and consequences.\n"
        f"- Maintain consistency with **Dungeons & Dragons lore and mechanics**.\n"
        f"- **Always respond in JSON format with the following structure:**\n\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "<Narrative response here as a single string, incorporating scene details, interaction type, and options (if any)>"\n'
        f"}}\n"
        f"```\n"
        f"- **Do not include any text outside of the JSON block. Only provide the JSON response.**\n\n"
        f"**Example of Expected Response:**\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "The sun sets over the tranquil village of Everwood as you, Aria the Elven Ranger, return from a day of scouting. The scent of pine lingers in the crisp evening air. As you approach the village square, a hush falls over the townsfolk, and all eyes turn to the distant horizon where ominous storm clouds gather. Suddenly, the town elder approaches you with a grave expression. \\"A darkness is coming, Aria,\\" he whispers. \\"We need your help.\\"\\n\\nOptions:\\n1. Agree to help and ask for more details about the impending darkness.\\n2. Climb the tallest tree to get a better view of the approaching storm.\\n3. Rally the villagers to prepare defenses.\\n4. Seek out your old mentor who lives on the outskirts of the village for guidance.\\n5. Use a secret passage you discovered as a child to venture toward the storm and investigate alone."\n'
        f"}}\n"
        f"```\n"
    )


def continue_campaign_prompt(context, previous_storyline, user_input):
    return (
        f"You are the Dungeon Master (DM) for an ongoing Dungeons & Dragons 5th Edition campaign. "
        f"Continue the story based on the player's input and maintain consistency with their game preferences.\n\n"
        f"**Player Preferences and Character Details:**\n{context}\n\n"
        f"**Previous Storyline:**\n{previous_storyline}\n\n"
        f"Respond to the player's input in your response.\n"
        f"**Player Input:**\n{user_input}\n\n"
        f"**Instructions:**\n"
        f"- Use varying scene descriptions, shifting between intense encounters and quiet, suspenseful moments.\n"
        f"- Alternate between interaction types:\n"
        f"  - **Dialogue choices** when speaking with NPCs.\n"
        f"  - **Skill challenges** (e.g., stealth, perception) to introduce risks and rewards.\n"
        f"  - **Open-ended exploration** to allow the player freedom in their actions.\n"
        f"- Build suspense by adding mysteries or foreshadowing events based on past player choices.\n"
        f"- Include moments of reflection, emotional depth, or stakes that resonate with the player's character.\n"
        f"- **Always respond in JSON format:**\n\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "<Your narrative response here as a single string>"\n'
        f"}}\n"
        f"```\n"
        f"- **Do not include any text outside of the JSON block. Only provide the JSON response.**\n\n"
        f"**Examples of Expected Responses:**\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "You decide to rally the villagers to prepare defenses. The town square buzzes with activity as you assign tasks: barricading entrances, sharpening weapons, and setting up watchtowers. The villagers look to you with a mix of fear and hope. As night falls, a distant howl pierces the silence, sending a chill down everyone\'s spine. Suddenly, a shadowy figure emerges from the forest edge.\\n\\nOptions:\\n1. Confront the figure and demand its identity.\\n2. Order the archers to ready their bows and await your signal.\\n3. Encourage the villagers to stand firm and not show fear.\\n4. Use your knowledge of the forest to set a trap for any approaching threats.\\n5. Secretly leave the village to seek out the source of the howl alone."\n'
        f"}}\n"
        f"```\n"
    )


def validate_storyline_prompt(context, storyline):
    return (
        f"Your task is to review the campaign storyline for alignment with the player's game preferences, ensuring immersive and engaging narration that flows consistently with previous events.\n\n"
        f"**Player Preferences and Character Details:**\n{context}\n\n"
        f"**Storyline:**\n{storyline}\n\n"
        f"**Instructions:**\n"
        f"1. Verify that the storyline maintains consistency with the player's preferences (e.g., tone, theme, difficulty level) and previous storyline context.\n"
        f"2. Ensure the narrative is immersive and progresses effectively, with rich descriptions, appropriate pacing, and intriguing developments.\n"
        f"3. Identify any aspects of the storyline that might break immersion, create inconsistencies, or contradict the player's established preferences.\n"
        f"4. Avoid focusing on detailed D&D 5th Edition rules unless they directly impact the storyline's believability or immersion.\n"
        f"5. **Only provide feedback if there are misalignments with preferences, narrative inconsistencies, stalled progression, or issues with immersion quality.**\n\n"
        f"**Response Format:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "<Your feedback here, if any>"\n'
        f"}}\n"
        f"```\n\n"
        f"**Examples of Feedback:**\n"
        f"- **Example of theme misalignment:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "The storyline introduces a spaceship, which conflicts with the player\'s preference for a medieval fantasy theme."\n'
        f"}}\n"
        f"```\n"
        f"- **Example of difficulty misalignment:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "The challenges presented are too easy, not matching the player\'s preference for a hard difficulty setting."\n'
        f"}}\n"
        f"```\n"
        f"- **Example of stalled progression:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "The storyline seems repetitive without introducing new elements, which may hinder narrative engagement."\n'
        f"}}\n"
        f"```\n"
        f"- **Example of an immersion issue:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "The storyline includes modern dialogue that feels out of place in a medieval fantasy setting, which could disrupt immersion."\n'
        f"}}\n"
        f"```\n"
    )


def validate_options_prompt(context, dm_prompt):
    return (
        f"Review the Dungeon Master's response to ensure the provided options align with the player's abilities, character context, and the scene setting, in accordance with D&D 5th Edition rules.\n\n"
        f"**Player Preferences and Character Details:**\n{context}\n\n"
        f"**DM's Response (Scene and Options):**\n{dm_prompt}\n\n"
        f"**Instructions:**\n"
        f"1. Confirm that each option aligns with the player’s character abilities, class, and D&D 5th Edition rules.\n"
        f"2. Ensure options are appropriate and realistic within the context of the current scene (e.g., environmental details, character’s current state).\n"
        f"3. Identify any options that imply abilities or actions the player’s character cannot perform or that would break immersion in the scene.\n"
        f"4. **Only provide feedback if any options are inconsistent with the player’s abilities, the game rules, or the scene context.**\n\n"
        f"**Response Format:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "<Your feedback here, if any>"\n'
        f"}}\n"
        f"```\n\n"
        f"**Examples of Feedback:**\n"
        f"- **Example of invalid option due to class abilities:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "The option to \'Cast Fireball\' is not valid, as the player\'s character, a Level 1 Ranger, cannot cast Fireball."\n'
        f"}}\n"
        f"```\n"
        f"- **Example of option inconsistent with scene context:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "The option to \'Climb a tree to get a better view\' is inconsistent, as the scene describes the player being in a cave with no trees nearby."\n'
        f"}}\n"
        f"```\n"
        f"- **Example of immersion-breaking action:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "The option to \'Summon a magical helicopter\' is immersion-breaking and does not align with the medieval fantasy theme of the game."\n'
        f"}}\n"
        f"```\n"
    )


def revise_options_prompt(context, dm_response, feedback):
    return (
        f"You are the Dungeon Master (DM) revising your previous response based on feedback. Ensure that all options are appropriate for the scene, align with the player’s abilities, and enhance immersion.\n\n"
        f"**Player Preferences and Character Details:**\n{context}\n\n"
        f"**Current DM's Response (Scene and Options):**\n{dm_response}\n\n"
        f"**Feedback:**\n{feedback}\n\n"
        f"**Instructions:**\n"
        f"- Adjust the options to ensure they align with the character's abilities, class, and the D&D 5th Edition rules.\n"
        f"- Ensure the options are consistent with the environmental context of the scene.\n"
        f"- Avoid breaking immersion with actions that do not fit the game’s theme.\n"
        f"- **Always respond in JSON format with the following structure:**\n\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "<Your revised narrative response here>"\n'
        f"}}\n"
        f"```\n\n"
        f"**Examples of Revised Responses:**\n"
        f"- **Scene-Aligned Option Revision Example:**\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "The cave grows darker as you approach the mysterious sound.\\n\\nOptions:\\n1. Approach the sound cautiously with your weapon drawn.\\n2. Use your ranger skills to analyze the sound from a safe distance.\\n3. Try to move silently closer, hoping to avoid detection.\\n4. Shout a warning into the darkness, hoping to elicit a response.\\n5. Retreat from the cave, opting for caution and safety."\n'
        f"}}\n"
        f"```\n"
    )


def inform_invalid_action_prompt(context, dm_response, user_input, feedback):
    return (
        f"Provide feedback to the player about their chosen action, explaining why it is invalid based on their abilities, the scene context, or D&D 5th Edition rules. Suggest alternative actions they could consider within the constraints of the scene.\n\n"
        f"**Player Preferences and Character Details:**\n{context}\n\n"
        f"**DM's Last Response (Scene and Options):**\n{dm_response}\n\n"
        f"**Player Input (Chosen Action):**\n{user_input}\n\n"
        f"**Feedback:**\n{feedback}\n\n"
        f"**Instructions:**\n"
        f"- Briefly explain why the chosen action is not possible or inconsistent with the character's abilities or the scene.\n"
        f"- Offer two to three alternative actions the player could consider, suited to their abilities and the context.\n"
        f"- **Respond in JSON format with the following structure:**\n\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "<Your explanation and suggested actions here>"\n'
        f"}}\n"
        f"```\n\n"
        f"**Example of Response:**\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "As a Level 1 Ranger, you do not have the ability to cast Fireball. However, you can consider the following actions: \\n1. Draw your bow and prepare to defend against the unknown threat.\\n2. Attempt to use your survival skills to analyze the sound and determine its origin.\\n3. Try to move silently closer to the sound to gather more information."\n'
        f"}}\n"
        f"```\n"
    )


def validate_player_action_prompt(context, dm_response, user_input):
    return (
        f"Review the player's chosen action to verify it is valid based on their character's abilities, the context of the DM's response, and D&D 5th Edition rules.\n\n"
        f"**Player Preferences and Character Details:**\n{context}\n\n"
        f"**DM's Last Response (Scene and Options):**\n{dm_response}\n\n"
        f"**Player Input (Chosen Action):**\n{user_input}\n\n"
        f"**Instructions:**\n"
        f"1. Confirm that the player's chosen action aligns with their character’s abilities, class, and D&D 5th Edition rules.\n"
        f"2. Assess whether the action is reasonable and consistent within the scene and options presented by the DM.\n"
        f"3. If the action is invalid, suggest a similar action that fits within their abilities and aligns with the scene.\n"
        f"4. **Only provide feedback if the action is invalid.**\n\n"
        f"**Response Format:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "<Your feedback here, if any>"\n'
        f"}}\n"
        f"```\n\n"
        f"**Examples of Feedback:**\n"
        f"- **Example of invalid action due to spellcasting limitations:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "The player attempted to cast Fireball, which is invalid as a Level 1 Ranger. Recommend actions such as \'draw your bow\' or \'use stealth\'."\n'
        f"}}\n"
        f"```\n"
        f"- **Example of action inconsistent with scene context:**\n"
        f"```json\n"
        f"{{\n"
        f'  "feedback": "The player chose to \'climb a tree for a better view,\' but the scene describes them being inside a cave. Recommend an action within the cave context, such as \'explore the cave further\' or \'approach the sound cautiously.\'"\n'
        f"}}\n"
        f"```\n"
    )


def revise_storyline_prompt(context, storyline, feedback):
    return (
        f"You are the Dungeon Master (DM) revising your previous response based on narrative feedback, ensuring the storyline aligns with the player's preferences and immersion is maintained.\n\n"
        f"**Player Preferences and Character Details:**\n{context}\n\n"
        f"**Current Storyline:**\n{storyline}\n\n"
        f"**Feedback:**\n{feedback}\n\n"
        f"**Instructions:**\n"
        f"- Adjust the storyline to address the narrative feedback, revising any parts as necessary to fit the player's preferences.\n"
        f"- Focus on enhancing immersion, continuity, and atmosphere in alignment with the player’s chosen theme and tone.\n"
        f"- Maintain continuity with previous events and create a consistent, cohesive storyline.\n"
        f"- Avoid altering actions or scenes unless specifically prompted by feedback; retain the player’s agency wherever possible.\n"
        f"- **Always respond in JSON format with the following structure:**\n\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "<Your revised narrative response here>"\n'
        f"}}\n"
        f"```\n\n"
        f"**Examples of Revised Responses:**\n"
        f"- **Narrative Adjustment Example:**\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "You take a deep breath and focus your senses, drawing upon your soldier training. The eerie whispers of the forest intensify, but this time, you notice patterns in the sounds—signals used by goblin scouts. Realizing you\'re being watched, you swiftly devise a plan.\\n\\nOptions:\\n1. Set a trap using your surroundings to ambush the goblins.\\n2. Signal your allies to prepare for an imminent attack.\\n3. Attempt to communicate with the goblins, hoping to negotiate.\\n4. Use stealth to quietly relocate and observe the goblins unnoticed.\\n5. Mimic the goblin signals to confuse and mislead them."\n'
        f"}}\n"
        f"```\n"
        f"- **Scene Adjustment Example (when the scene is misaligned with preferences):**\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "The wind howls as you emerge into the forest clearing. You pause, feeling the eerie quiet around you, only to spot the faint glow of torchlight in the distance.\\n\\nOptions:\\n1. Approach the light with caution.\\n2. Scout the area for any hidden threats.\\n3. Attempt to remain unseen and move closer to observe.\\n4. Ready your weapon and move in for a potential confrontation."\n'
        f"}}\n"
        f"```\n"
    )


def format_feedback_prompt(expected_keys):
    # Dynamically generate the JSON format example based on expected keys
    json_example = ",\n".join([f'  "{key}": "value"' for key in expected_keys])

    return (
        f"Error: The last response had incorrect formatting.\n\n"
        f"Your response was not delivered because it was in the wrong format.\n"
        f"Do not apologize or include any extra text. Please resend your previous response, ensuring it complies with the required JSON format.\n"
        f"You must respond in JSON with the following keys:\n"
        f"**Expected JSON Keys:**\n{expected_keys}\n\n"
        f"**Required Format:**\n"
        f"```json\n"
        f"{{\n{json_example}\n}}\n"
        f"```\n"
        f"- **Do not include any text outside of the JSON block.**\n\n"
        f"**Incorrect Format Example:**\n"
        f"```\n"
        f"Sure, here is my response:\n\nThe hero enters the dark cave...\n```\n"
        f"**Correct Format Example:**\n"
        f"```json\n"
        f"{{\n"
        f'  "dm_response": "The hero enters the dark cave, the air thick with the scent of damp earth. A faint glow emanates from deep within..."'
        f"}}\n"
        f"```\n"
    )
