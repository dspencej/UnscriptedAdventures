# llm/prompts.py


def create_campaign_prompt(user_input, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"As the DMAgent, your task is to create a **new campaign** that aligns with the user’s input and preferences. You will generate an initial storyline and provide the first response to start the campaign.\n\n"
        f"**User Input:**\n{user_input}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Storyline Generation:** Create a cohesive and engaging campaign storyline based on the user's input and preferences.\n"
        f"- **First Response:** Provide a brief starting response for the user to begin their adventure.\n"
        f"- **Maintain Alignment:** Ensure that the campaign's tone, theme, and difficulty are consistent with the preferences specified.\n"
        f"- **Response Format:** Use **only** the JSON format provided below. If the response cannot be generated, return an empty JSON with placeholders.\n"
        f"```json\n"
        f"{{\n"
        f'  "storyline": "<Generated storyline>",\n'
        f'  "dm_response": "<Response to the user>"\n'
        f"}}\n"
        f"```\n"
    )


def continue_campaign_prompt(context, previous_storyline, user_input, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"As the DMAgent, your task is to respond to the user's input while considering the ongoing campaign, user preferences, and previous events.\n\n"
        f"**User Input:**\n{user_input}\n\n"
        f"**Conversation Context:**\n{context}\n\n"
        f"**Previous Storyline:**\n{previous_storyline}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Respond to Input:** Answer user questions, narrate interactions, or extend the storyline as appropriate based on the user’s input.\n"
        f"- **Narrate Consequences:** If the user takes an action, describe the consequences and how it affects the campaign environment or characters.\n"
        f"- **Maintain Context:** Ensure that the response remains consistent with the previous storyline, user preferences, and current context.\n"
        f"- **Adapt to User Actions:** While not every response needs to progress the campaign, ensure that it reflects user input and provides an engaging interaction.\n"
        f"- **Response Format:** Provide the response in the exact JSON format below. If no storyline progression occurs, leave the storyline field as an empty string.\n"
        f"```json\n"
        f"{{\n"
        f'  "storyline": "<Continued storyline or leave empty>",\n'
        f'  "dm_response": "<Response to the user>"\n'
        f"}}\n"
        f"```\n"
    )


def validate_storyline_prompt(context, storyline, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"As the StorytellerAgent, your task is to validate the campaign storyline generated by the DMAgent, ensuring it aligns with the user's preferences and the current campaign context.\n\n"
        f"**Conversation Context:**\n{context}\n\n"
        f"**Storyline:**\n{storyline}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Validate Storyline:** Ensure that the storyline aligns with the user’s preferences in terms of tone, genre, and progression. Confirm consistency with past events and narrative flow.\n"
        f"- **Provide Constructive Feedback:** If any inconsistencies or gaps are identified, provide specific feedback to guide necessary revisions. Feedback should be actionable and focused on improving coherence or alignment with preferences.\n"
        f"- **Response Format:** Provide feedback in the exact JSON format below. If everything is aligned, set consistency_check to 'Yes' and leave feedback empty.\n"
        f"```json\n"
        f"{{\n"
        f'  "consistency_check": "<Yes/No>",\n'
        f'  "feedback": "<Any issues or areas for revision or leave empty>"\n'
        f"}}\n"
        f"```\n"
    )


def revise_campaign_prompt(context, feedback, user_preferences):
    preferences_text = "\n".join(
        [f"- {key}: {value}" for key, value in user_preferences.items()]
    )
    return (
        f"As the DMAgent, you have received feedback from the StorytellerAgent regarding the campaign's storyline. Your task is to revise the storyline based on the feedback while considering the user’s preferences and input.\n\n"
        f"**Conversation Context:**\n{context}\n\n"
        f"**Storyteller Feedback:**\n{feedback}\n\n"
        f"**User Preferences:**\n{preferences_text}\n\n"
        f"**Instructions:**\n"
        f"- **Revise Storyline:** Adjust the storyline based on the feedback, ensuring the changes align with user preferences and resolve the issues raised.\n"
        f"- **Narrate the Outcome:** Provide a response that reflects the revised storyline and acknowledges any significant changes.\n"
        f"- **Maintain Engagement:** Keep the user engaged with an interesting and consistent response, whether you are revising major events or making subtle adjustments.\n"
        f"- **Ensure Coherence:** Ensure that the revised storyline continues to make sense within the overall narrative, and that it aligns with previous events and user preferences.\n"
        f"- **Response Format:** Provide the revised storyline in the JSON format below. If there are no major changes to the storyline, leave the revised_storyline field empty.\n"
        f"```json\n"
        f"{{\n"
        f'  "revised_storyline": "<Revised campaign storyline or leave empty>",\n'
        f'  "dm_response": "<Response to the user after revision>"\n'
        f"}}\n"
        f"```\n"
    )


def format_feedback_prompt(agent_name):
    return (
        f"Error: The last response from {agent_name} could not be parsed due to incorrect formatting.\n\n"
        f"Please resend the response in proper JSON format, ensuring all required fields are included.\n"
        f"Do not include any extra greetings or apologies. Resend your response with the proper formatting.\n"
        f"```json\n"
        f"{{\n"
        f'  "key": "value",\n'
        f"}}\n"
        f"```"
    )


def feedback_missing_storyline(agent_name):
    return (
        f"Error: The last response from {agent_name} did not include a storyline.\n\n"
        f"Please ensure that every response contains a valid storyline, even if no major events occur. Summarize the current situation or provide minor narrative details to maintain the flow of the campaign.\n"
        f"Resend your response in proper JSON format, ensuring the 'storyline' field is filled.\n"
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
        f"Please revise the storyline to resolve these inconsistencies. Ensure that the tone, genre, and progression remain consistent with the user's preferences, and that the storyline logically follows the previous events.\n"
        f"Resend your response in the proper format below.\n"
        f"```json\n"
        f"{{\n"
        f'  "revised_storyline": "<Corrected storyline>",\n'
        f'  "dm_response": "<Response to the user>"\n'
        f"}}\n"
        f"```"
    )
