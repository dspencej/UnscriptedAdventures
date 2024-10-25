# llm/prompts.py
def router_agent_prompt(
    preferences_text, context, sender, message_content, agents_descriptions
):
    # Build the agents descriptions text
    agents_descriptions_text = ""
    for agent_name, description in agents_descriptions.items():
        agents_descriptions_text += f"- **{agent_name}**: {description}\n\n"

    # Build the list of agents excluding the sender
    recipients = [agent for agent in agents_descriptions.keys() if agent != sender]
    recipients.append("User")  # Ensure 'User' is included
    recipients_text = ", ".join(recipients)

    prompt = f"""As the RouterAgent, your responsibility is to determine the next recipient (agent or user) of a message.

User Preferences:
{preferences_text}

Conversation Context:
{context}Sender: {sender}
Message Content:
\"\"\"
{message_content}
\"\"\"

Agent Descriptions:
{agents_descriptions_text}

Instructions:
- Based on the sender and message content, decide where the message should go next.
- **Important:** Do not route the message back to the sender.
- Choose one of the following recipients (excluding the sender): {recipients_text}.
- Respond with your decision in the following JSON format:
{{
  "next_recipient": "<Agent name or 'User'>"
}}

Example response (if sender is '{sender}'):
{{
  "next_recipient": "RuleExpertAgent"
}}
"""
    return prompt


def assistant_agent_prompt(context, user_input):
    return (
        f"As the AssistantAgent, your role is to handle all out-of-character (OOC) responses and messages that do not fit well with other specialized agents.\n\n"
        f"Conversation Context:\n{context}"
        f'User\'s Input:\n"""\n{user_input}\n"""\n\n'
        f"Instructions:\n"
        f"- Provide a direct and helpful response to the user's OOC input.\n"
        f"- Ensure responses are clear, concise, and maintain the game's serious tone.\n"
        f"- Choose one of the following recipients: 'User', or another agent if appropriate.\n"
        f"- Indicate who you are trying to send your message to by including 'next_recipient' in your response.\n"
        f"- Respond in the following JSON format:\n"
        f"{{\n"
        f'  "next_recipient": "<Recipient name>",\n'
        f'  "assistant_response": "<Your response here>"\n'
        f"}}\n"
        f"\n"
        f"Example response:\n"
        f"{{\n"
        f'  "next_recipient": "User",\n'
        f'  "assistant_response": "I\'m here to assist you with any questions or issues you might have."\n'
        f"}}\n"
    )


def rule_expert_prompt(context, user_input):
    return (
        f"As the RuleExpertAgent, your task is to determine if the user's intended action is allowed according to D&D "
        f"rules and if the user is capable of performing it.\n\n"
        f"Conversation Context:\n{context}"
        f'User\'s Intended Action:\n"""\n{user_input}\n"""\n\n'
        f"Instructions:\n"
        f"- Analyze the user's action for rule compliance and capability.\n"
        f"- Provide a response indicating whether the action is **exactly** 'allowed' or 'not allowed'.\n"
        f"- Include any relevant rule explanations or requirements.\n"
        f"- Choose one of the following recipients: 'DMAgent' or 'User'.\n"
        f"- Indicate who you are trying to send your message to by including 'next_recipient' in your response.\n"
        f"- Respond in the following JSON format:\n"
        f"{{\n"
        f'  "next_recipient": "<Recipient name>",\n'
        f'  "action_allowed": "<allowed/not allowed>",\n'
        f'  "rule_explanation": "<Your explanation here>"\n'
        f"}}\n"
        f"\n"
        f"Example response:\n"
        f"{{\n"
        f'  "next_recipient": "DMAgent",\n'
        f'  "action_allowed": "allowed",\n'
        f'  "rule_explanation": "The user can attempt to jump across the ravine with a successful Athletics check."\n'
        f"}}\n"
    )


def dm_agent_prompt(context, user_input):
    return (
        f"As the DMAgent, your role is to interpret the player's action and respond directly to the player.\n\n"
        f"Conversation Context:\n{context}"
        f"Player's Action:\n{user_input}\n\n"
        f"Instructions:\n"
        f"- If the action is not permitted, inform the player why.\n"
        f"- If the action is allowed, acknowledge the action and provide a brief summary.\n"
        f"- Respond directly to the player with clear and concise information.\n"
        f"- Respond in the following format:\n"
        f"{{\n"
        f'  "dm_response": "<Your response to the player>"\n'
        f"}}\n"
        f"\n"
        f"Example response when the action is not allowed:\n"
        f"{{\n"
        f'  "dm_response": "You cannot fly across the canyon without wings or magic."\n'
        f"}}\n"
        f"\n"
        f"Example response when the action is allowed:\n"
        f"{{\n"
        f'  "dm_response": "You leap across the ravine with a mighty jump."\n'
        f"}}\n"
    )


def storyteller_prompt(context, dm_summary):
    return (
        f"As the StorytellerAgent, provide a vivid narrative based on the user's action.\n\n"
        f"Conversation Context:\n{context}"
        f"DMAgent's Summary:\n{dm_summary}\n\n"
        f"Instructions:\n"
        f"- Continue the story with immersive descriptions.\n"
        f"- Maintain consistency and engagement.\n"
        f"- Address the user directly.\n"
        f"- Set 'next_recipient' to 'User' as you are continuing the story for them.\n"
        f"- Provide your narrative as 'storyteller_response'.\n"
        f"- Respond in the following JSON format:\n"
        f"{{\n"
        f'  "next_recipient": "User",\n'
        f'  "storyteller_response": "<Your narrative here>"\n'
        f"}}\n"
        f"\n"
        f"Example response:\n"
        f"{{\n"
        f'  "next_recipient": "User",\n'
        f'  "storyteller_response": "As you leap across the ravine, the wind whistles past your ears..."\n'
        f"}}\n"
    )


def agent_feedback_prompt(agent_name, error_message, original_prompt):
    return (
        f"As the {agent_name}, there was an issue with your previous response.\n"
        f"Error: {error_message}\n\n"
        f"Please review your response and correct it according to the instructions.\n"
        f"Remember:\n"
        f"- Follow the instructions carefully.\n"
        f"- Ensure your response is in the correct format.\n"
        f"- Do not include any disallowed content.\n"
        f"- Indicate who you are trying to send your message to by including 'next_recipient' in your response.\n\n"
        f"---\n"
        f'Original Prompt:\n"""\n{original_prompt}\n"""\n'
    )
