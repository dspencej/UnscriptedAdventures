import portalocker
from flask import Flask, render_template, request, jsonify, session
import random
import json
import os
import asyncio
import uuid
from llm_agent import generate_gm_response
from flask_session import Session
import logging

app = Flask(__name__)

# Use environment variable for secret key and secure configuration
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = './.flask_session/'
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # Enable this when using HTTPS in production

# Ensure the session directory exists
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

# Initialize Flask-Session
Session(app)

# File paths for saving character and game data
CHARACTER_FILE = 'characters.json'
GAME_STATE_FILE = 'game_state.json'

# Helper functions for file locking with portalocker
def safe_open_file(filename, mode='r'):
    try:
        file = open(filename, mode)
        portalocker.lock(file, portalocker.LOCK_EX)  # Lock the file to avoid race conditions
        return file
    except (IOError, OSError) as e:
        app.logger.error(f"Error opening file {filename}: {e}")
        return None

def safe_close_file(file):
    try:
        portalocker.unlock(file)
        file.close()
    except (IOError, OSError) as e:
        app.logger.error(f"Error closing file: {e}")

# Load existing character data
def load_characters():
    if os.path.exists(CHARACTER_FILE):
        file = safe_open_file(CHARACTER_FILE, 'r')
        if file:
            try:
                content = file.read().strip()
                return json.loads(content) if content else []
            except json.JSONDecodeError as e:
                app.logger.error(f"Error decoding JSON from {CHARACTER_FILE}: {e}")
                return []
            finally:
                safe_close_file(file)
    return []

# Save character data to the file
def save_characters(characters):
    file = safe_open_file(CHARACTER_FILE, 'w')
    if file:
        try:
            json.dump(characters, file)
        except (TypeError, IOError) as e:
            app.logger.error(f"Error saving character data to {CHARACTER_FILE}: {e}")
        finally:
            safe_close_file(file)

# Load the game state
def load_game_state():
    if os.path.exists(GAME_STATE_FILE):
        file = safe_open_file(GAME_STATE_FILE, 'r')
        if file:
            try:
                content = file.read().strip()
                return json.loads(content) if content else {}
            except json.JSONDecodeError as e:
                app.logger.error(f"Error decoding JSON from {GAME_STATE_FILE}: {e}")
                return {}
            finally:
                safe_close_file(file)
    return {}

# Save the game state
def save_game_state(game_state):
    file = safe_open_file(GAME_STATE_FILE, 'w')
    if file:
        try:
            json.dump(game_state, file)
        except (TypeError, IOError) as e:
            app.logger.error(f"Error saving game state to {GAME_STATE_FILE}: {e}")
        finally:
            safe_close_file(file)

# Define the GameEnvironment class
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

# Define the GameMasterAgent class
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
        app.logger.info(f"GM chooses to: {self.current_strategy}")
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
    user_input = request.json.get('user_input', '').strip()

    if not user_input:
        return jsonify({"status": "error", "message": "Input cannot be empty!"}), 400

    app.logger.info(f"User input: {user_input}")

    conversation_id = session.get('conversation_id', str(uuid.uuid4()))
    session['conversation_id'] = conversation_id

    user_preferences = session.get('user_preferences', {})
    gm_prompt = f"You are the Game Master in a text-based RPG. Consider these preferences:\n"

    for key, value in user_preferences.items():
        gm_prompt += f"- {key}: {value}\n"

    gm_prompt += f"\nThe player input: '{user_input}'. Respond accordingly."

    try:
        gm_response = asyncio.run(generate_gm_response(gm_prompt))
    except Exception as e:
        app.logger.error(f"Error in GM response generation: {e}")
        return jsonify({"status": "error", "message": "Error generating GM response."}), 500

    game_state = load_game_state()
    if conversation_id not in game_state:
        game_state[conversation_id] = {'conversation': [], 'preferences': user_preferences}

    game_state[conversation_id]['conversation'].append({'role': 'user', 'content': user_input})
    game_state[conversation_id]['conversation'].append({'role': 'gm', 'content': gm_response})
    save_game_state(game_state)

    response_data = {
        'gm_response': gm_response,
        'conversation_history': game_state[conversation_id]['conversation']
    }

    return jsonify(response_data)

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
