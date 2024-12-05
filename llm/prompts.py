# llm/prompts.py
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_campaign_prompt(user_input, context):
    return f"""
    You are the Game Master (GM) for a campaign in a role-playing game based on the player's preferences and 5th Edition mechanics. Create an immersive, consistent world setting while introducing a compelling storyline.

    **Player Preferences, Character Details and the context of the game:**
    {context}

    **Player Input:**
    {user_input}

    **Instructions:**
    1. Begin with a **rich, vivid scene description** to set the tone and atmosphere. Include sensory details such as:
        - **Visual elements** (colors, textures, movement)
        - **Sounds** (background noises, specific auditory cues)
        - **Scents** (environmental smells, noticeable aromas)
        - **Textures or sensations** (ambient temperature, weather, tactile elements)
    2. Provide potential **interaction options** within the scene, such as:
        - **Dialogue choices** for conversations with NPCs.
        - **Skill checks** (e.g., perception, insight, investigation) to build tension or reveal hidden details.
        - **Open-ended exploration** for player freedom.
    3. Drive the narrative forward at a good, reasonable pace - not too quick or too slow.
    4. Maintain continuity with previous player actions to build a cohesive storyline, weaving in prior events.
    5. Use **5E mechanics** as a basis for responses.
    6. **JSON Response Format Requirement**:
        - Only respond in JSON format.
        - Use the format below, with no extra keys or explanations:

    ```json
    {{
        "response": "<Narrative response as a single string. Ensure nested dialogue is enclosed in single quotes, e.g., 'He said, Hello!' Do not include line breaks or extra whitespace inside this field.>"
    }}
    ```

    **Correct Example:**
    ```json
    {{
        "response": "The town square bustles with activity as vendors shout their wares. A guard eyes you warily and says, 'Greetings, traveler. What brings you here?'"
    }}
    ```
    """


def continue_campaign_prompt(context, previous_storyline, user_input):
    return f"""
    You are the Game Master (GM) for an ongoing campaign in a role-playing game. Continue the story based on the player's input while maintaining consistency with their preferences and established storyline.

    **Player Preferences and Character Details:**
    {context}

    **Current Storyline:**
    {previous_storyline}

    **Player Input:**
    {user_input}

    **Instructions:**
    1. Start with a **detailed, immersive scene description**. Include sensory details that align with the established setting:
        - **Visuals** (colors, textures, movement).
        - **Sounds** (ambient noises, specific auditory cues).
        - **Scents** (aromas or environmental smells).
        - **Textures or sensations** (weather, tactile elements).
    2. Offer **interaction options** within the scene:
        - **Dialogue choices** for conversations with NPCs.
        - **Skill challenges** (e.g., stealth, perception) to create tension.
        - **Exploration opportunities** to allow player freedom.
    3. Follow storytelling conventions:
        - Add **narrative hooks** to provide options without forcing a specific path.
        - Include **foreshadowing** to build suspense or intrigue.
        - Balance intense moments with **rest or discovery** opportunities.
    4. Drive the narrative forward at a good, reasonable pace - not too quick or too slow.
    5. Do NOT reveal GM-only information, such as DCs or hidden mechanics.
    6. Assume the player knows their character's basic information, so avoid repeating it.

    **JSON Response Requirement**:
    - **Respond ONLY in JSON format** using the structure below.
    - Follow this exact format to ensure proper JSON parsing:

    ```json
    {{
        "response": "<Your narrative response here as a single string. Include sensory details, interaction options, and maintain storyline continuity. Use single quotes for nested dialogue (e.g., 'He said, Hello!'). Do not include line breaks or extra whitespace within this field.>"
    }}
    ```

    **Correct JSON Example:**
    ```json
    {{
        "response": "As you step into the shadowy forest, the crunch of leaves underfoot echoes around you. A hooded figure steps forward and says, 'Greetings, traveler. What brings you to these woods?'"
    }}
    ```
    """


def validate_storyline_prompt(context, storyline, dm_response):
    return f"""
    Your task is to review the campaign storyline for alignment with the player's preferences, ensuring it is immersive, consistent, and engaging.

    **Player Preferences and Character Details:**
    {context}

    **Current Storyline:**
    {storyline}
    
    **New GM Response:**
    {dm_response}

    **Instructions:**
    1. Verify that the storyline aligns with the player's preferences, including tone, theme, and difficulty, and that it remains consistent with previous context.
    2. Confirm that the narrative is immersive and flows smoothly, with rich descriptions, appropriate pacing, and well-crafted scenes.
    3. Ensure the GM’s response adheres to best practices for TTRPG storytelling, enhancing the player's experience.
    4. Provide feedback only if you identify:
        - **Misalignments** with player preferences (e.g., unwanted tone shifts, inconsistencies with established elements),
        - **Narrative inconsistencies** or contradictions,
        - **Elements hindering immersion** (e.g., lack of sensory detail, unclear descriptions, or abrupt transitions).
    5. **Avoid suggesting major changes unless they are strictly necessary for consistency or player alignment.**

    6. **Response Format:**
    ```json
    {{
        "feedback": "<Your feedback here, or empty string if no feedback is needed>"
    }}
    ```

    7. **Do not include any text outside of the JSON block. Only provide the JSON response. Do not include nested keys.**
    """


def revise_storyline_prompt(context, storyline, previous_response, feedback):
    return f"""
    You are the Game Master (GM) revising your previous response based on feedback. Ensure the storyline aligns with the player's preferences and preserves immersion. 
    **Your response should retain all elements of the previous response, with only minimal adjustments based on the feedback.**
    
    **Player Preferences and Character Details:**
    {context}
    
    **Current Storyline:**
    {storyline}
    
    **Previous Response:**
    {previous_response}
    
    **Feedback:**
    {feedback}
    
    **Instructions:**
    1. Retain the original description closely; make only small adjustments, such as adding details or shifting tone slightly.
    2. Maintain all key elements from the previous response (e.g., objects, characters, atmosphere).
    3. Enhance immersion by adding minor sensory details or descriptive elements if needed.
    4. Avoid introducing new items, locations, or actions unless explicitly requested in the feedback.
    5. **Respond in JSON format only, using the structure below:**
    ```json
    {{
        "response": "<Your revised narrative response here>"
    }}
    ```
    6. **Do not include any text outside of the JSON block. Only provide the JSON response. Do not include nested keys.**
    """


def validate_options_prompt(context, dm_prompt):
    logger.debug("validate_options_prompt")
    return f"""
    Review the GM's response to ensure that all options provided align with the player's abilities, character details, and the current scene context.

    **Player Preferences and Character Details:**
    {context}

    **GM's Response (Scene and Options):**
    {dm_prompt}

    **Instructions:**
    1. Check that each option provided by the GM is realistic, consistent with the character's abilities, class, and standard 5th Edition rules.
    2. Verify that the options align with the current scene and setting, enhancing immersion rather than disrupting it.
    3. Identify any options that propose actions beyond the character’s capabilities or that could break immersion within the scene.
    4. **Only provide feedback if inconsistencies are detected regarding abilities, rules, or scene context.** If everything aligns, set `"feedback"` to an empty string.

    5. **Response Format:**
        - Respond strictly with a JSON object containing only the `feedback` key, with no nested keys or additional fields.
        - If feedback is necessary, provide it within the `feedback` field. If no feedback is needed, set `feedback` to an empty string (`""`).

    6. **Required JSON Response Format (strict adherence):**
    ```json
    {{
        "feedback": "<Your feedback here, or an empty string if no feedback is needed>"
    }}
    ```

    7. **Important:**
        - Your response must strictly match the format above, with only the `feedback` key in the JSON object. Do not include any extra text, explanations, or keys outside of the JSON block.
        - Do not include nested keys.
    """


def revise_options_prompt(context, dm_response, feedback):
    logger.debug("revise_options_prompt")
    return f"""
    You are the Game Master (GM) revising your previous response based on feedback. Retain the structure and content of your original response, but make specific adjustments to address the feedback provided.
    
    **Player Preferences and Character Details:**
    {context}
    
    **Original GM Response:**
    {dm_response}
    
    **Feedback to Address:**
    {feedback}
    
    **Instructions:**
    1. Keep your response as close to the original as possible.
    2. Adjust the options only as needed to incorporate the feedback.
    3. Ensure the options are consistent with the environmental context of the scene.
    4. Maintain immersion by aligning actions with the game’s themeR.
    5. **Always respond in JSON format with the following structure:**
    ```json
    {{
        "response": "<Your revised narrative response here>"
    }}
    ```
    6. **Do not include any text outside of the JSON block. Only provide the JSON response. Do not include nested keys.**
    """


def inform_invalid_action_prompt(context, storyline, user_input):
    logger.debug("inform_invalid_action_prompt")
    return f"""
    Provide feedback to the player about why their chosen action is invalid based on their abilities, class, or 5th Edition rules. Suggest alternative actions they could consider that are appropriate for their character.
    
    **Player Preferences and Character Details:**
    {context}
    
    **Storyline:**
    {storyline}
    
    **Player's Input (Chosen Action):**
    {user_input}
    
    **Instructions:**
    1. Briefly explain why the chosen action is not possible due to the character's abilities or 5th Edition rules.
    2. Offer a few alternative actions the player could consider, suited to their abilities.
    3. **Do not** consider the action's consistency with the scene or narrative context. Strictly evaluate its compliance with the rules.
    4. **Respond in JSON format** with the following structure, using the key 'response' and no nested keys:
    ```json
    {{
        "response": "<Your explanation and suggested actions here>"
    }}
    ```
    5. **Do not include any text outside of the JSON block. Only provide the JSON response. Do not include nested keys.**
    """


def validate_player_action_prompt(context, dm_response, user_input):
    logger.debug("validate_player_action_prompt")
    return f"""
    Your task is to evaluate the player's chosen action and determine whether it is valid based on their character's abilities, class, and 5th Edition rules.
    
    **Player Preferences and Character Details:**
    {context}
    
    **Current Conversation and Scene:**
    {dm_response}
    
    **Player's Input (Chosen Action):**
    {user_input}
    
    **Instructions:**
    1. Determine if the player's action is valid for their character's class and abilities under 5th Edition rules.
    2. Allow the player to have creative freedom provided they are in compliance with 5th edition rules.
    3. Allow the player to ask questions of the GM.
    4. If the action is **valid**, respond with JSON containing an empty string for feedback:
    ```json
    {{
        "feedback": ""
    }}
    ```
    5. If the action is **invalid** (e.g., the character attempts to use a spell or ability they do not have), respond with feedback explaining **why** the action is invalid and suggest a few alternative actions that are appropriate for their character.
    6. When generating the list of alternative actions make sure to only use characters that are appropriate in  JSON format: (Replace * with -)
    7. Don't forget to close a bracketed list with ] if you start one with [
    8. Remember to always close your JSON response with a closing curly bracket
    9. **Response Format:**
    ```json
    {{
        "feedback": "<Your feedback here>"
    }}
    ```
    10. **Do not include any text outside of the JSON block. Only provide the JSON response. Do not include nested keys.**
    """


def format_feedback_prompt(expected_keys, previous_response):
    logger.debug("format_feedback_prompt")
    # Generate JSON example with all expected keys
    json_lines = [
        f'"{key}": "<original response without nested quotation marks>"'
        for key in expected_keys
    ]
    json_example = ",\n        ".join(json_lines)

    correct_json_lines = [
        f'"{key}": "The guard eyes you warily and says, \'Greetings, traveler.\'"'
        for key in expected_keys
    ]
    correct_json_example = ", ".join(correct_json_lines)

    return f"""Your previous response did not meet the correct JSON format.

        **Original GM Response:**
        {previous_response}

    **Instructions:**
    1. Keep your response as close to the original as possible while correcting for proper JSON encoding.
    2. Use exactly these keys: **{', '.join(expected_keys)}**.
    3. **Each key must have a value**, even if it's an empty string ("").
    4. **The value must be a single string**: avoid line breaks, use single quotes for nested dialogue (e.g., 'He said, Hello!'), and ensure no extra whitespace.
    5. **Escape special characters properly**, including double quotes (\"), backslashes (\\), and newlines (\\n).
    6. **Return only the JSON block** with the specified keys. Do not add explanations, additional keys, or any text outside the JSON block.
    7. **Respond using the exact JSON format below**:

        **Required JSON Format:**
        ```json
        {{
            {json_example}
        }}
        ```
        **Correct JSON Format:**
        ```json
        {{
            {correct_json_example}
        }}
        ```
"""

def extract_entities_prompt(text_corpus):
    return f"""
    Your task is to analyze the provided text corpus and extract all relevant entities that should be included in a knowledge graph. Focus on identifying proper nouns, important concepts, and significant terms related to the context.

    **Text Corpus:**
    {text_corpus}

    **Instructions:**
    1. Identify and list all unique entities present in the text.
    2. Categorize each entity based on its type (e.g., Person, Location, Organization, Event, etc.).
    3. Ensure that entities are accurately extracted without duplicates.
    4. Present the extracted entities in a JSON array with each entity having a `name` and `type`.

    **JSON Response Format:**
    ```json
    [
        {{
            "name": "Entity Name",
            "type": "Entity Type"
        }},
        ...
    ]
    ```
    """
def map_relationships_prompt(entities, text_corpus):
    return f"""
    Your task is to analyze the provided text corpus and identify relationships between the given entities. Use the entities extracted previously to determine how they are connected within the context.

    **Entities:**
    {entities}

    **Text Corpus:**
    {text_corpus}

    **Instructions:**
    1. Identify all meaningful relationships between the entities.
    2. For each relationship, specify the `source`, `target`, and `relationship_type`.
    3. Ensure that the relationships accurately reflect the interactions or associations described in the text.
    4. Present the relationships in a JSON array with each relationship having `source`, `target`, and `relationship_type`.

    **JSON Response Format:**
    ```json
    {{
        {", ".join(['"{}": "The guard eyes you warily and says, \'Greetings, traveler.\'"'.format(key) for key in expected_keys])}
    }}
    ```
    """

