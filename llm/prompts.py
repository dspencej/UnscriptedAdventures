# llm/prompts.py

def create_campaign_prompt(user_input, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"Your task is to start a new storyline that aligns with the user's game style preferences.\n"
        f"Do not ask the user for input on the campaign. Instead, use the preferences below to craft a new story for the player.\n"
        f"Narrate the scene and respond to the user's actions and decisions.\n\n"
        f"**User Input:**\n{user_input}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Storyline Generation:** Craft a cohesive and engaging campaign storyline based on the user's preferences.\n"
        f"  - Match the tone, theme, and difficulty with user preferences (e.g., dark fantasy, high-stakes adventure).\n\n"
        f"- **Starting Scene Creation:** Create a vivid opening scene description that immerses players.\n"
        f"  - Include sensory details (sights, sounds, smells) to enhance the atmosphere.\n"
        f"  - Present a clear environment without dictating the player's choices or tasks.\n\n"
        f"- **Consistency:** Ensure all campaign elements (tone, pacing, difficulty) align with user preferences.\n\n"
        f"- Do not introduce yourself. They know that you are the DM.\n\n"
        f"- **Response Format:** Output should be in JSON format, without introductory text. Follow this structure:\n\n"
        f"```json\n"
        f"{{\n"
        f'  "storyline": "<Generated campaign storyline>",\n'
        f'  "dm_response": "<Initial scene description without player tasks>"\n'
        f"}}\n"
        f"```"
    )



def continue_campaign_prompt(context, previous_storyline, user_input, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"Your task is to respond to the user's input while considering the ongoing campaign and user preferences.\n\n"
        f"**User Input:**\n{user_input}\n\n"
        f"**Conversation Context:**\n{context}\n\n"
        f"**Previous Storyline:**\n{previous_storyline}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Respond to Input:** Address the user's questions and narrate interactions based on their input.\n"
        f"- **Narrate Consequences:** Describe the consequences of user actions and their impact on the campaign.\n"
        f"- **Maintain Context:** Ensure responses align with the previous storyline, user preferences, and context.\n"
        f"- **Adapt to User Actions:** Responses should reflect user input, enhancing engagement without always progressing the storyline.\n"
        f"- **Response Format:** Provide the response in JSON format. If no storyline progression is needed, leave the storyline field empty:\n"
        f"```json\n"
        f"{{\n"
        f'  "storyline": "<Continued storyline or leave empty>",\n'
        f'  "dm_response": "<Response to the user>"\n'
        f"}}\n"
        f"```"
    )


def validate_storyline_prompt(context, storyline, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"The Dungeon Master has provided a storyline progression for the campaign. Your task is to validate this storyline based on user preferences and context.\n"
        f"Ensure the storyline is self-consistent.\n\n"
        f"**Conversation Context:**\n{context}\n\n"
        f"**Storyline:**\n{storyline}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Evaluate the Storyline:** Check for alignment with user preferences regarding tone, genre, and progression. Ensure consistency with past events.\n"
        f"- **Provide Constructive Feedback:** If inconsistencies are found, offer specific, actionable feedback to guide revisions, focusing on coherence and alignment with preferences.\n"
        f"- **Response Format:** Your feedback should be in JSON format. If no adjustments are needed, set `consistency_check` to 'Yes' and leave `feedback` empty:\n"
        f"```json\n"
        f"{{\n"
        f'  "consistency_check": "<Yes/No>",\n'
        f'  "feedback": "<Any issues or areas for revision or leave empty>"\n'
        f"}}\n"
        f"```"
    )



def revise_campaign_prompt(context, storyline, feedback, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"You have received feedback on the campaign's storyline. Your task is to revise it based on this feedback while considering user preferences.\n\n"
        f"**Conversation Context:**\n{context}\n\n"
        f"**Storyline Feedback:**\n{feedback}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Storyline to Revise:**\n{storyline}\n\n"
        f"**Instructions:**\n"
        f"- **Revise the Storyline:** Make adjustments according to the feedback, ensuring they align with user preferences and address the issues raised.\n"
        f"- **Maintain Engagement:** Craft an engaging response, whether through major changes or subtle adjustments, to keep the user invested.\n"
        f"- **Ensure Coherence:** Verify that the revised storyline remains logical within the overall narrative, connecting seamlessly with past events and user preferences.\n"
        f"- **Response Format:** Provide the revised storyline in JSON format. This format is crucial:\n"
        f"```json\n"
        f"{{\n"
        f'  "revised_storyline": "<Revised campaign storyline or leave empty>",\n'
        f'  "dm_response": "<Response to the user after revision>"\n'
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
