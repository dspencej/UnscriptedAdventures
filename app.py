from flask import Flask, render_template, request, jsonify, session
import random
import json
import os
import asyncio
from llm_agent import generate_gm_response  # Import the LLM function from llm_agent

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required to use sessions

# File paths for saving character and game data
CHARACTER_FILE = 'characters.json'
GAME_STATE_FILE = 'game_state.json'


# Load existing character data
def load_characters():
    if os.path.exists(CHARACTER_FILE):
        with open(CHARACTER_FILE, 'r') as file:
            try:
                content = file.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return []
            except json.JSONDecodeError:
                print("Error: JSON data is invalid or corrupted.")
                return []
    return []


# Save character data to the file
def save_characters(characters):
    with open(CHARACTER_FILE, 'w') as file:
        json.dump(characters, file)


# Load the game state
def load_game_state():
    if os.path.exists(GAME_STATE_FILE):
        with open(GAME_STATE_FILE, 'r') as file:
            try:
                content = file.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return {}
            except json.JSONDecodeError:
                print("Error: JSON data is invalid or corrupted.")
                return {}
    return {}


# Save the game state
def save_game_state(game_state):
    with open(GAME_STATE_FILE, 'w') as file:
        json.dump(game_state, file)


class GameEnvironment:
    def __init__(self):
        self.player_engagement = 0

    def player_feedback(self, response):
        if response == "positive":
            return random.uniform(0.5, 1.0)
        elif response == "neutral":
            return random.uniform(0.2, 0.5)
        else:
            return random.uniform(0.0, 0.2)


class GameMasterAgent:
    def __init__(self):
        self.reward_history = []
        self.current_strategy = "introduce_quest"
        self.strategy_rewards = {
            "introduce_quest": 0.5,
            "introduce_npc": 0.5,
            "introduce_conflict": 0.5
        }

    def choose_strategy(self):
        best_strategy = max(self.strategy_rewards, key=self.strategy_rewards.get)
        return best_strategy

    def update_strategy_rewards(self, feedback_score):
        self.reward_history.append(feedback_score)
        if feedback_score > 0.6:
            self.strategy_rewards[self.current_strategy] += 0.1
        else:
            self.strategy_rewards[self.current_strategy] -= 0.1

    def perform_action(self):
        self.current_strategy = self.choose_strategy()
        print(f"DM chooses to: {self.current_strategy}")
        return self.current_strategy


environment = GameEnvironment()
dm_agent = GameMasterAgent()


@app.route('/')
def index():
    current_character = session.get('current_character', None)
    return render_template('index.html', current_character=current_character)


@app.route('/interact', methods=['POST'])
def interact():
    # Safely get user input from the request JSON
    user_input = request.json.get('user_input', '').strip()  # Default to an empty string if key is missing

    # Check if user_input is empty
    if not user_input:
        return jsonify({"status": "error", "message": "Input cannot be empty!"}), 400  # Return a 400 Bad Request

    app.logger.info(f"User input: {user_input}")

    # Generate a prompt for the LLM
    gm_prompt = f"You are the Game Master in a text-based RPG game. The player says: '{user_input}'. Respond appropriately."

    # Use asyncio to run the asynchronous function
    gm_response = asyncio.run(generate_gm_response(gm_prompt))
    app.logger.info(f"GM Response: {gm_response}")

    # Prepare response data
    response_data = {
        'gm_response': gm_response
    }

    return jsonify(response_data)


@app.route('/save_game', methods=['POST'])
def save_game():
    game_state = request.json.get('game_state', {})
    save_game_state(game_state)
    return jsonify({"status": "success", "message": "Game saved successfully!"})


@app.route('/game_preferences')
def game_preferences():
    """Render the game preference form."""
    return render_template('game_preferences.html')

@app.route('/submit_preferences', methods=['POST'])
def submit_preferences():
    """Handle the submission of game preferences."""
    preferences = request.json.get('preferences', {})

    # Create a prompt for the LLM based on user preferences
    llm_prompt = f"User preferences:\n"
    for key, value in preferences.items():
        llm_prompt += f"{key}: {value}\n"
    llm_prompt += "Start a game based on these preferences."

    # Send this prompt to the LLM
    gm_response = asyncio.run(generate_gm_response(llm_prompt))
    app.logger.info(f"GM Response to Preferences: {gm_response}")

    # Store the game context in the session or save it
    session['game_context'] = gm_response

    return jsonify({"status": "success", "message": "Preferences submitted successfully!", "gm_response": gm_response})

@app.route('/load_game', methods=['GET'])
def load_game():
    game_state = load_game_state()
    conversation_history = game_state.get('conversation', [])

    if conversation_history:
        # Prepare the prompt by concatenating the entire conversation history
        llm_prompt = "You are the Game Master in a text-based RPG game. Here is the conversation so far:\n\n"
        for entry in conversation_history:
            if entry['role'] == 'user':
                llm_prompt += f"Player: {entry['content']}\n"
            else:
                llm_prompt += f"GM: {entry['content']}\n"

        # Use asyncio to run the asynchronous function
        gm_response = asyncio.run(generate_gm_response(llm_prompt))
        app.logger.info(f"GM Response after loading game: {gm_response}")

        # Update the game state with the latest GM response
        conversation_history.append({'role': 'gm', 'content': gm_response})
        save_game_state({'conversation': conversation_history})

        return jsonify({"status": "success", "game_state": {'conversation': conversation_history}})
    else:
        return jsonify({"status": "error", "message": "No saved game found."})



@app.route('/character_creation')
def character_creation():
    return render_template('character_creation.html')


@app.route('/save_character', methods=['POST'])
def save_character():
    character_data = request.json
    characters = load_characters()
    characters.append(character_data)
    save_characters(characters)
    return jsonify({"status": "success", "message": "Character saved successfully!"})


@app.route('/manage_characters')
def manage_characters():
    characters = load_characters()
    current_character = session.get('current_character', None)
    return render_template('manage_characters.html', characters=characters, current_character=current_character)


@app.route('/select_character/<int:character_id>', methods=['GET'])
def select_character(character_id):
    characters = load_characters()
    if 0 <= character_id < len(characters):
        selected_character = characters[character_id]
        session['current_character'] = selected_character
        return jsonify({"status": "success", "character": selected_character})
    return jsonify({"status": "error", "message": "Character not found!"})


@app.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    characters = load_characters()
    if 0 <= character_id < len(characters):
        deleted_character = characters.pop(character_id)
        save_characters(characters)
        if session.get('current_character') == deleted_character:
            session.pop('current_character', None)
        return jsonify({"status": "success", "message": "Character deleted successfully!"})
    return jsonify({"status": "error", "message": "Character not found!"})


@app.route('/save_current_character', methods=['POST'])
def save_current_character():
    current_character = session.get('current_character', None)
    if current_character:
        characters = load_characters()
        for i, character in enumerate(characters):
            if character['name'] == current_character['name']:
                characters[i] = current_character
                save_characters(characters)
                return jsonify({"status": "success", "message": "Current character saved successfully!"})
        characters.append(current_character)
        save_characters(characters)
        return jsonify({"status": "success", "message": "Current character saved successfully!"})
    return jsonify({"status": "error", "message": "No current character to save!"})


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    print(f"Received contact form submission: Name={name}, Email={email}, Message={message}")
    return render_template('contact.html', success=True)


if __name__ == '__main__':
    app.run(debug=True)
