from flask import Flask, render_template, request, jsonify, session
import random
import json
import os
import asyncio
import uuid  # Import uuid to generate unique identifiers
from llm_agent import generate_gm_response  # Import the LLM function from llm_agent
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required to use sessions
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions in the server's filesystem
app.config['SESSION_PERMANENT'] = False  # Sessions should not persist indefinitely
app.config['SESSION_FILE_DIR'] = './.flask_session/'  # Directory for storing session files
app.config['SESSION_USE_SIGNER'] = True  # Encrypt the session cookie for security
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production over HTTPS

# Ensure the session directory exists
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

# Initialize Flask-Session
Session(app)

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
    conversation_history = session.get('conversation_history', [])
    return render_template('index.html', current_character=current_character, conversation_history=conversation_history)

@app.route('/interact', methods=['POST'])
def interact():
    user_input = request.json['user_input'].strip()

    # Handle empty input
    if not user_input:
        return jsonify({"status": "error", "message": "Input cannot be empty!"}), 400

    app.logger.info(f"User input: {user_input}")

    # Retrieve conversation_id from session or create a new one
    conversation_id = session.get('conversation_id')
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        session['conversation_id'] = conversation_id

    # Retrieve saved user preferences from the session
    user_preferences = session.get('user_preferences', {})

    gm_prompt = (
        "You are the Game Master in a text-based RPG game. Your role is to create a dynamic and engaging experience based on the player's preferences and actions. "
        "Consider the following user preferences when crafting your response:\n"
    )

    for key, value in user_preferences.items():
        gm_prompt += f"- {key}: {value}\n"

    gm_prompt += (
        f"\nThe player has provided the following input: '{user_input}'. "
        "Respond in a way that aligns with the user's preferences and continues the narrative."
    )

    # Use asyncio to run the asynchronous function
    gm_response = asyncio.run(generate_gm_response(gm_prompt))
    app.logger.info(f"GM Response: {gm_response}")

    # Maintain the conversation history using the unique conversation ID
    game_state = load_game_state()
    if conversation_id not in game_state:
        game_state[conversation_id] = {
            'conversation': [],
            'preferences': user_preferences
        }

    game_state[conversation_id]['conversation'].append({'role': 'user', 'content': user_input})
    game_state[conversation_id]['conversation'].append({'role': 'gm', 'content': gm_response})
    save_game_state(game_state)

    # Prepare response data
    response_data = {
        'gm_response': gm_response,
        'conversation_history': game_state[conversation_id]['conversation']
    }

    return jsonify(response_data)

@app.route('/game_preferences')
def game_preferences():
    """Render the game preference form."""
    return render_template('game_preferences.html')

@app.route('/submit_preferences', methods=['POST'])
def submit_preferences():
    """Handle the submission of game preferences."""
    preferences = request.json.get('preferences', {})

    # Save preferences in the session
    session['user_preferences'] = preferences

    # Prepare an initial response or acknowledgement
    response_message = "Preferences submitted successfully! Your game will be customized accordingly."

    return jsonify({"status": "success", "message": response_message})

@app.route('/save_game', methods=['POST'])
def save_game():
    """Save the current game state, including preferences and conversation history."""
    conversation_id = session.get('conversation_id')
    if not conversation_id:
        return jsonify({"status": "error", "message": "No active game to save."}), 400

    game_state = load_game_state()
    user_preferences = session.get('user_preferences', {})

    # If no conversation exists for the session, initialize it
    if conversation_id not in game_state:
        game_state[conversation_id] = {
            'conversation': [],
            'preferences': user_preferences
        }

    # Update game state with preferences and conversation history
    game_state[conversation_id]['preferences'] = user_preferences
    save_game_state(game_state)

    return jsonify({"status": "success", "message": "Game saved successfully!"})

@app.route('/load_game', methods=['GET'])
def load_game():
    """Load a saved game and restore conversation history and preferences."""
    conversation_id = session.get('conversation_id')
    if not conversation_id:
        return jsonify({"status": "error", "message": "No saved game found."}), 404

    game_state = load_game_state()
    if conversation_id in game_state:
        session['conversation_history'] = game_state[conversation_id].get('conversation', [])
        session['user_preferences'] = game_state[conversation_id].get('preferences', {})
        return jsonify({"status": "success", "message": "Game loaded successfully!"})
    else:
        return jsonify({"status": "error", "message": "No saved game found."}), 404

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
