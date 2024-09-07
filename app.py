from flask import Flask, render_template, request, jsonify, session
import random
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required to use sessions

# File path for saving character data
CHARACTER_FILE = 'characters.json'

# Load existing character data
# Load existing character data
def load_characters():
    if os.path.exists(CHARACTER_FILE):
        with open(CHARACTER_FILE, 'r') as file:
            try:
                # Check if the file is not empty before loading
                content = file.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return []
            except json.JSONDecodeError:
                # Handle JSON decode error if the file is corrupted
                print("Error: JSON data is invalid or corrupted.")
                return []
    return []

# Save character data to the file
def save_characters(characters):
    with open(CHARACTER_FILE, 'w') as file:
        json.dump(characters, file)

# Example environment setup
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

# Example Agent: Dungeon Master (DM)
class DungeonMasterAgent:
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

# Initialize game environment and DM agent
environment = GameEnvironment()
dm_agent = DungeonMasterAgent()

@app.route('/')
def index():
    current_character = session.get('current_character', None)
    return render_template('index.html', current_character=current_character)

@app.route('/interact', methods=['POST'])
def interact():
    user_input = request.json['user_input']
    strategy = dm_agent.perform_action()
    feedback_score = environment.player_feedback(user_input)
    dm_agent.update_strategy_rewards(feedback_score)
    response = {
        'dm_action': strategy,
        'feedback_score': feedback_score,
        'updated_rewards': dm_agent.strategy_rewards
    }
    return jsonify(response)

# Corrected Route for Character Creation
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
        # If the deleted character is the current character, remove it from the session
        if session.get('current_character') == deleted_character:
            session.pop('current_character', None)
        return jsonify({"status": "success", "message": "Character deleted successfully!"})
    return jsonify({"status": "error", "message": "Character not found!"})

@app.route('/save_current_character', methods=['POST'])
def save_current_character():
    current_character = session.get('current_character', None)
    if current_character:
        characters = load_characters()
        # Check if the character already exists in the list, if so, update it
        for i, character in enumerate(characters):
            if character['name'] == current_character['name']:
                characters[i] = current_character
                save_characters(characters)
                return jsonify({"status": "success", "message": "Current character saved successfully!"})
        # If character does not exist, add it as a new character
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
    # Handle the form submission
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    # For now, just print the submitted data to the console
    print(f"Received contact form submission: Name={name}, Email={email}, Message={message}")

    # You can implement further logic here, such as saving the data or sending an email

    return render_template('contact.html', success=True)


if __name__ == '__main__':
    app.run(debug=True)
