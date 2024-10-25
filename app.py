import asyncio
import json
import logging
import os

import portalocker
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session

# Import generate_gm_response from the llm package
from llm.llm_agent import generate_gm_response

app = Flask(__name__)

# Use environment variable for secret key and secure configuration
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_COOKIE_SECURE"] = (
    False  # Set to True when using HTTPS in production
)

# Ensure the session directory exists
if not os.path.exists(app.config["SESSION_FILE_DIR"]):
    os.makedirs(app.config["SESSION_FILE_DIR"])

# Initialize Flask-Session
Session(app)

# File paths for saving character and preferences data
CHARACTER_FILE = "characters.json"
PREFERENCES_FILE = "user_preferences.json"


# Helper functions for file locking with portalocker
def safe_open_file(filename, mode="r"):
    try:
        file = open(filename, mode)
        portalocker.lock(
            file, portalocker.LOCK_EX
        )  # Lock the file to avoid race conditions
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
        file = safe_open_file(CHARACTER_FILE, "r")
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
    file = safe_open_file(CHARACTER_FILE, "w")
    if file:
        try:
            json.dump(characters, file)
        except (TypeError, IOError) as e:
            app.logger.error(f"Error saving character data to {CHARACTER_FILE}: {e}")
        finally:
            safe_close_file(file)


# Load user preferences from file
def load_preferences():
    if os.path.exists(PREFERENCES_FILE):
        file = safe_open_file(PREFERENCES_FILE, "r")
        if file:
            try:
                return json.load(file)
            except json.JSONDecodeError as e:
                app.logger.error(f"Error decoding JSON from {PREFERENCES_FILE}: {e}")
                return {}
            finally:
                safe_close_file(file)
    return {}


# Save preferences to file
def save_preferences(preferences):
    file = safe_open_file(PREFERENCES_FILE, "w")
    if file:
        try:
            json.dump(preferences, file)
        except (TypeError, IOError) as e:
            app.logger.error(f"Error saving preferences to {PREFERENCES_FILE}: {e}")
        finally:
            safe_close_file(file)


@app.route("/")
def index():
    current_character = session.get("current_character", None)
    # Initialize conversation_history in session if it doesn't exist
    if "conversation_history" not in session:
        session["conversation_history"] = []
    conversation_history = session.get("conversation_history")
    return render_template(
        "index.html",
        current_character=current_character,
        conversation_history=conversation_history,
    )


@app.route("/interact", methods=["POST"])
def interact():
    user_input = request.json.get("user_input", "").strip()

    if not user_input:
        return jsonify({"status": "error", "message": "Input cannot be empty!"}), 400

    app.logger.info(f"User input: {user_input}")

    # Retrieve user preferences and conversation history from the session
    user_preferences = session.get("user_preferences", {})
    conversation_history = session.get("conversation_history", [])
    storyline = session.get("storyline", "")

    try:
        # Use a new event loop for asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        gm_response = loop.run_until_complete(
            generate_gm_response(
                user_input, conversation_history, user_preferences, storyline
            )
        )
        loop.close()

        # Log the GM response for debugging
        app.logger.debug(f"GM response: {gm_response}")

        # Store the new storyline if it's returned in the GM response
        if isinstance(gm_response, dict):
            if "full_storyline" in gm_response:
                storyline = gm_response["full_storyline"]
                session["storyline"] = storyline  # Update storyline in session

            if "dm_response" in gm_response:
                gm_response_text = gm_response["dm_response"]
            else:
                gm_response_text = "Unknown response"

    except Exception as e:
        app.logger.error(f"Error in GM response generation: {e}")
        return jsonify(
            {"status": "error", "message": "Error generating GM response."}
        ), 500

    # Update conversation history in the session
    session["conversation_history"] = conversation_history

    # Append user input and GM response to the conversation history
    session["conversation_history"].append({"role": "user", "content": user_input})
    session["conversation_history"].append({"role": "gm", "content": gm_response_text})

    # Mark the session as modified to ensure changes are saved
    session.modified = True

    response_data = {"gm_response": gm_response_text}
    return jsonify(response_data)


@app.route("/new_game", methods=["POST"])
def new_game():
    session["conversation_history"] = []
    session.modified = True
    return jsonify({"message": "New game started."})


@app.route("/clear_game", methods=["POST"])
def clear_game():
    session["conversation_history"] = []
    session.modified = True
    return jsonify({"message": "Game display cleared."})


@app.route("/save_game", methods=["POST"])
def save_game():
    # Save the conversation history to a file (or database)
    game_state = session.get("conversation_history", [])
    try:
        with open("saved_game.json", "w") as f:
            json.dump(game_state, f)
        return jsonify({"message": "Game saved successfully."})
    except Exception as e:
        app.logger.error(f"Error saving game: {e}")
        return jsonify({"message": "Error saving game."}), 500


@app.route("/load_game", methods=["GET"])
def load_game():
    try:
        with open("saved_game.json", "r") as f:
            game_state = json.load(f)
        session["conversation_history"] = game_state
        session.modified = True
        return jsonify(
            {
                "status": "success",
                "message": "Game loaded successfully.",
                "game_state": game_state,
            }
        )
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "No saved game found."}), 404
    except Exception as e:
        app.logger.error(f"Error loading game: {e}")
        return jsonify({"status": "error", "message": "Error loading game."}), 500


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/submit_contact", methods=["POST"])
def submit_contact():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    # Process the data (e.g., send an email or log the message)

    # Redirect to the thank-you page after processing the form
    return redirect(url_for("thank_you"))


@app.route("/character_creation")
def character_creation():
    return render_template("character_creation.html")


@app.route("/save_character", methods=["POST"])
def save_character():
    character_data = request.json  # Get the character data sent from the frontend

    # Basic validation to ensure all fields are present
    if not all(
        [
            character_data.get("name"),
            character_data.get("race"),
            character_data.get("class"),
            character_data.get("background"),
        ]
    ):
        return jsonify({"message": "All fields are required!"}), 400

    characters = load_characters()  # Load existing characters from the file

    # Save the new character
    characters.append(character_data)
    save_characters(characters)  # Save the updated character list back to the file

    # Return success message
    return jsonify({"message": "Character saved successfully!"})


@app.route("/thank_you")
def thank_you():
    return render_template("thank_you.html")


@app.route("/manage_characters")
def manage_characters():
    characters = load_characters()  # Load existing characters from the file
    return render_template("manage_characters.html", characters=characters)


@app.route("/select_character/<int:character_id>")
def select_character(character_id):
    characters = load_characters()

    if character_id < len(characters):
        selected_character = characters[character_id]
        session["current_character"] = (
            selected_character  # Set current character in session
        )
        session.modified = True
        return jsonify({"status": "success", "character": selected_character})
    else:
        return jsonify({"status": "error", "message": "Character not found"}), 404


@app.route("/delete_character/<int:character_id>", methods=["POST"])
def delete_character(character_id):
    characters = load_characters()

    if character_id < len(characters):
        deleted_character = characters.pop(character_id)
        save_characters(characters)  # Save updated character list
        return jsonify(
            {
                "status": "success",
                "message": f"Character {deleted_character['name']} deleted successfully!",
            }
        )
    else:
        return jsonify({"status": "error", "message": "Character not found"}), 404


@app.route("/save_current_character", methods=["POST"])
def save_current_character():
    current_character = session.get("current_character")

    if not current_character:
        return jsonify({"status": "error", "message": "No character to save"}), 400

    characters = load_characters()

    # Update the existing character or append a new one
    for i, char in enumerate(characters):
        if char["name"] == current_character["name"]:
            characters[i] = current_character
            break
    else:
        characters.append(current_character)

    save_characters(characters)  # Save updated character list
    return jsonify(
        {"status": "success", "message": "Current character saved successfully!"}
    )


# Game Preferences Routes
@app.route("/game_preferences")
def game_preferences():
    # Load the saved preferences (if available)
    preferences = load_preferences()
    session["user_preferences"] = preferences  # Store preferences in session
    session.modified = True
    return render_template("game_preferences.html", preferences=preferences)


@app.route("/submit_preferences", methods=["POST"])
def submit_preferences():
    preferences_data = request.json.get("preferences", {})

    # Basic validation to ensure all fields are provided
    if not all(
        [
            preferences_data.get("gameStyle"),
            preferences_data.get("tone"),
            preferences_data.get("difficulty"),
            preferences_data.get("theme"),
        ]
    ):
        return jsonify({"message": "All preferences are required!"}), 400

    # Save preferences to file
    save_preferences(preferences_data)

    # Store preferences in session
    session["user_preferences"] = preferences_data
    session.modified = True

    # Send a success response
    return jsonify({"message": "Preferences saved successfully!"})


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
