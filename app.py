import asyncio
import json
import logging
import os

from colorama import Fore, Style
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_migrate import Migrate
from flask_session import Session

# Import ORM models
from llm.llm_agent import generate_gm_response
from models.character_models import Background, Character, Class, Race, db
from models.character_models import populate_defaults as populate_character_defaults
from models.game_preferences_models import GamePreferences
from models.game_preferences_models import populate_defaults as populate_game_defaults
from models.save_game_models import SavedGame

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

# Database configuration (single database)
basedir = os.path.abspath(os.path.dirname(__file__))
db_file = os.path.join(basedir, "characters.db")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_file

# Initialize the single db instance
db.init_app(app)

# Set up migrations for the single database
migrate = Migrate(app, db)

# Initialize Flask-Session
Session(app)


@app.route("/")
def index():
    try:
        current_character = session.get("current_character", None)
        if "conversation_history" not in session:
            session["conversation_history"] = []
        conversation_history = session.get("conversation_history")

        app.logger.debug(
            f"{Fore.MAGENTA}Loading index page.\n"
            f"{Fore.CYAN}Current character: {current_character}\n"
            f"Conversation history: {conversation_history}{Style.RESET_ALL}"
        )

        return render_template(
            "index.html",
            current_character=current_character,
            conversation_history=conversation_history,
        )
    except Exception as e:
        app.logger.error(f"{Fore.RED}Error in index route: {e}{Style.RESET_ALL}")
        return jsonify({"status": "error", "message": "Error loading index page."}), 500


@app.route("/interact", methods=["POST"])
def interact():
    try:
        user_input = request.json.get("user_input", "").strip()

        if not user_input:
            app.logger.warning(f"{Fore.YELLOW}Empty input received{Style.RESET_ALL}")
            return jsonify(
                {"status": "error", "message": "Input cannot be empty!"}
            ), 400

        # Retrieve user preferences and conversation history from the session
        user_preferences = session.get("user_preferences", {})
        if not user_preferences:
            app.logger.warning(
                f"{Fore.YELLOW}Game preferences not configured.{Style.RESET_ALL}"
            )
            return jsonify(
                {"status": "error", "message": "Game preferences have not been set!"}
            ), 400
        conversation_history = session.get("conversation_history", [])
        storyline = session.get("storyline", "")
        current_character = session.get("current_character", {})
        if not current_character:
            app.logger.warning(f"{Fore.YELLOW}No character selected.{Style.RESET_ALL}")
            return jsonify(
                {"status": "error", "message": "Please load a character!"}
            ), 400

        app.logger.info(f"{Fore.MAGENTA}Generating GM Response:{Style.RESET_ALL}")
        app.logger.debug(f"{Fore.CYAN}User Input: {user_input}{Style.RESET_ALL}")
        app.logger.debug(
            f"{Fore.CYAN}User Preferences: {user_preferences}{Style.RESET_ALL}"
        )
        app.logger.debug(
            f"{Fore.CYAN}Conversation History: {conversation_history}{Style.RESET_ALL}"
        )
        app.logger.debug(f"{Fore.CYAN}Storyline: {storyline}{Style.RESET_ALL}")
        app.logger.debug(
            f"{Fore.CYAN}Current Character: {current_character}{Style.RESET_ALL}"
        )

        # Use a new event loop for asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        gm_response = loop.run_until_complete(
            generate_gm_response(
                user_input,
                conversation_history,
                user_preferences,
                storyline,
                current_character,
            )
        )
        loop.close()

        # Log the GM response for debugging
        app.logger.debug(f"{Fore.GREEN}GM response: {gm_response}{Style.RESET_ALL}")

        # Store the new storyline if it's returned in the GM response
        if isinstance(gm_response, dict):
            storyline = gm_response.get("full_storyline", storyline)
            session["storyline"] = storyline  # Update storyline in session
            gm_response_text = gm_response.get("dm_response", "Unknown response")
        else:
            gm_response_text = "Unknown response"

        # Update conversation history in the session
        session["conversation_history"] = conversation_history
        session["conversation_history"].append({"role": "user", "content": user_input})
        session["conversation_history"].append(
            {"role": "gm", "content": gm_response_text}
        )
        session.modified = True

        app.logger.info(
            f"{Fore.GREEN}GM response generated and conversation history updated.{Style.RESET_ALL}"
        )

        response_data = {"gm_response": gm_response_text}
        return jsonify(response_data)
    except Exception as e:
        app.logger.error(
            f"{Fore.RED}Error in GM response generation: {e}{Style.RESET_ALL}"
        )
        return jsonify(
            {"status": "error", "message": "Error generating GM response."}
        ), 500


@app.route("/new_game", methods=["POST"])
def new_game():
    try:
        session["conversation_history"] = []
        session["user_preferences"] = []
        session["current_character"] = []
        session["storyline"] = []
        session.modified = True
        app.logger.info(
            f"{Fore.GREEN}New game started, conversation history cleared.{Style.RESET_ALL}"
        )
        return jsonify({"message": "New game started."})
    except Exception as e:
        app.logger.error(f"{Fore.RED}Error starting new game: {e}{Style.RESET_ALL}")
        return jsonify({"status": "error", "message": "Error starting new game."}), 500


@app.route("/about")
def about():
    try:
        app.logger.info(f"{Fore.MAGENTA}Loading about page.{Style.RESET_ALL}")
        return render_template("about.html")
    except Exception as e:
        app.logger.error(f"{Fore.RED}Error loading about page: {e}{Style.RESET_ALL}")
        return jsonify({"status": "error", "message": "Error loading about page."}), 500


@app.route("/contact")
def contact():
    try:
        app.logger.info(f"{Fore.MAGENTA}Loading contact page.{Style.RESET_ALL}")
        return render_template("contact.html")
    except Exception as e:
        app.logger.error(f"{Fore.RED}Error loading contact page: {e}{Style.RESET_ALL}")
        return jsonify(
            {"status": "error", "message": "Error loading contact page."}
        ), 500


@app.route("/submit_contact", methods=["POST"])
def submit_contact():
    try:
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        app.logger.info(
            f"{Fore.GREEN}Contact form submitted.\n"
            f"Name: {name}, Email: {email}{Style.RESET_ALL}"
            f"Message: {message}{Style.RESET_ALL}"
        )

        # Process the data (e.g., send an email or log the message)
        return redirect(url_for("thank_you"))
    except Exception as e:
        app.logger.error(
            f"{Fore.RED}Error submitting contact form: {e}{Style.RESET_ALL}"
        )
        return jsonify(
            {"status": "error", "message": "Error submitting contact form."}
        ), 500


@app.route("/character_creation")
def character_creation():
    try:
        races = Race.query.all()
        classes = Class.query.all()
        backgrounds = Background.query.all()

        app.logger.debug(
            f"{Fore.MAGENTA}Character creation page loaded.\n"
            f"{Fore.CYAN}Races: {races}, Classes: {classes}, Backgrounds: {backgrounds}{Style.RESET_ALL}"
        )

        return render_template(
            "character_creation.html",
            races=races,
            classes=classes,
            backgrounds=backgrounds,
        )
    except Exception as e:
        app.logger.error(
            f"{Fore.RED}Error loading character creation page: {e}{Style.RESET_ALL}"
        )
        return jsonify(
            {"status": "error", "message": "Error loading character creation page."}
        ), 500


@app.route("/save_character", methods=["POST"])
def save_character():
    try:
        character_data = request.json  # Get the character data sent from the frontend

        # Log the incoming data for debugging
        app.logger.debug(
            f"{Fore.CYAN}Received character data: {character_data}{Style.RESET_ALL}"
        )

        # Basic validation to ensure all fields are present
        if not all(
            [
                character_data.get("name"),
                character_data.get("race"),
                character_data.get("class"),
                character_data.get("background"),
            ]
        ):
            app.logger.warning(
                f"{Fore.YELLOW}Character save failed: All fields are required!{Style.RESET_ALL}"
            )
            return jsonify({"message": "All fields are required!"}), 400

        # Fetch the related race, class, and background from the database
        race = Race.query.filter_by(name=character_data["race"]).first()
        character_class = Class.query.filter_by(name=character_data["class"]).first()
        background = Background.query.filter_by(
            name=character_data["background"]
        ).first()

        if not race or not character_class or not background:
            app.logger.warning(
                f"{Fore.YELLOW}Invalid character data: {character_data}{Style.RESET_ALL}"
            )
            return jsonify({"message": "Invalid race, class, or background."}), 400

        app.logger.debug(
            f"{Fore.MAGENTA}Validated race, class, and background for character.{Style.RESET_ALL}"
        )

        # Create a new Character instance
        new_character = Character(
            name=character_data["name"],
            race=race,
            background=background,
            character_class=character_class,  # Assign class directly
            level=int(character_data.get("level", 1)),
            experience_points=int(character_data.get("experience_points", 0)),
            strength=int(character_data.get("strength", 10)),
            dexterity=int(character_data.get("dexterity", 10)),
            constitution=int(character_data.get("constitution", 10)),
            intelligence=int(character_data.get("intelligence", 10)),
            wisdom=int(character_data.get("wisdom", 10)),
            charisma=int(character_data.get("charisma", 10)),
            max_hit_points=int(character_data.get("max_hit_points", 10)),
            current_hit_points=int(character_data.get("current_hit_points", 10)),
            armor_class=int(character_data.get("armor_class", 10)),
            speed=int(character_data.get("speed", 30)),
        )

        db.session.add(new_character)

        try:
            db.session.commit()

            app.logger.info(
                f"{Fore.GREEN}Character {new_character.name} saved successfully.{Style.RESET_ALL}"
            )

            # Update the session with the newly created character
            session["current_character"] = {
                "id": new_character.id,
                "name": new_character.name,
                "race": new_character.race.name,
                "class": new_character.character_class.name,
                "background": new_character.background.name,
                "level": new_character.level,
                "experience_points": new_character.experience_points,
                "strength": new_character.strength,
                "dexterity": new_character.dexterity,
                "constitution": new_character.constitution,
                "intelligence": new_character.intelligence,
                "wisdom": new_character.wisdom,
                "charisma": new_character.charisma,
                "max_hit_points": new_character.max_hit_points,
                "current_hit_points": new_character.current_hit_points,
                "armor_class": new_character.armor_class,
                "speed": new_character.speed,
            }
            session.modified = True  # Mark session as modified

            return jsonify({"message": "Character saved successfully!"}), 201
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"{Fore.RED}Error saving character: {e}{Style.RESET_ALL}")
            return jsonify({"message": "Error saving character."}), 500
    except Exception as e:
        app.logger.error(
            f"{Fore.RED}Error in save_character route: {e}{Style.RESET_ALL}"
        )
        return jsonify({"status": "error", "message": "Error saving character."}), 500


@app.route("/manage_characters")
def manage_characters():
    try:
        # Query all characters from the database
        characters = Character.query.all()
        return render_template("manage_characters.html", characters=characters)
    except Exception as e:
        app.logger.error(f"{Fore.RED}Error managing characters: {e}{Style.RESET_ALL}")
        return jsonify(
            {"status": "error", "message": "Error managing characters."}
        ), 500


@app.route("/select_character/<int:character_id>")
def select_character(character_id):
    try:
        # Retrieve the character from the database by its ID
        character = db.session.get(Character, character_id)

        if character:
            # Serialize the character into a format suitable for session storage or response
            selected_character = {
                "id": character.id,
                "name": character.name,
                "race": character.race.name,
                "class": character.character_class.name,  # Access single-class directly
                "background": character.background.name,
                "level": character.level,
                "experience_points": character.experience_points,
                "strength": character.strength,
                "dexterity": character.dexterity,
                "constitution": character.constitution,
                "intelligence": character.intelligence,
                "wisdom": character.wisdom,
                "charisma": character.charisma,
                "max_hit_points": character.max_hit_points,
                "current_hit_points": character.current_hit_points,
                "armor_class": character.armor_class,
                "speed": character.speed,
            }

            session["current_character"] = (
                selected_character  # Set current character in session
            )
            session.modified = True
            return jsonify({"status": "success", "character": selected_character})
        else:
            return jsonify({"status": "error", "message": "Character not found"}), 404
    except Exception as e:
        app.logger.error(f"{Fore.RED}Error selecting character: {e}{Style.RESET_ALL}")
        return jsonify(
            {"status": "error", "message": "Error selecting character."}
        ), 500


@app.route("/delete_character/<int:character_id>", methods=["POST"])
def delete_character(character_id):
    try:
        character = db.session.get(Character, character_id)

        if character:
            # Retrieve and log current character details for debugging
            current_character = session.get("current_character", {})
            app.logger.debug(f"Current character in session: {current_character}")

            # Check if the current character in session matches the one being deleted
            if current_character and current_character.get("id") == character.id:
                session.pop("current_character", None)  # Remove character from session
                app.logger.debug(
                    f"{Fore.MAGENTA}Cleared current character {character.name} from session{Style.RESET_ALL}"
                )

            # Proceed to delete the character from the database
            db.session.delete(character)
            db.session.commit()

            return jsonify(
                {
                    "status": "success",
                    "message": f"Character {character.name} deleted successfully!",
                }
            )
        else:
            return jsonify({"status": "error", "message": "Character not found"}), 404
    except Exception as e:
        app.logger.error(f"{Fore.RED}Error deleting character: {e}{Style.RESET_ALL}")
        return jsonify({"status": "error", "message": "Error deleting character."}), 500



@app.route("/save_current_character", methods=["POST"])
def save_current_character():
    try:
        current_character = session.get("current_character")

        if not current_character:
            return jsonify({"status": "error", "message": "No character to save"}), 400

        character = db.session.get(Character, current_character["id"])

        if character:
            # Update character fields
            character.level = current_character.get("level", character.level)
            character.experience_points = current_character.get(
                "experience_points", character.experience_points
            )
            character.strength = current_character.get("strength", character.strength)
            character.dexterity = current_character.get(
                "dexterity", character.dexterity
            )
            character.constitution = current_character.get(
                "constitution", character.constitution
            )
            character.intelligence = current_character.get(
                "intelligence", character.intelligence
            )
            character.wisdom = current_character.get("wisdom", character.wisdom)
            character.charisma = current_character.get("charisma", character.charisma)
            character.max_hit_points = current_character.get(
                "max_hit_points", character.max_hit_points
            )
            character.current_hit_points = current_character.get(
                "current_hit_points", character.current_hit_points
            )
            character.armor_class = current_character.get(
                "armor_class", character.armor_class
            )
            character.speed = current_character.get("speed", character.speed)

            db.session.commit()

            return jsonify(
                {
                    "status": "success",
                    "message": "Current character updated successfully!",
                }
            )
        else:
            return jsonify({"status": "error", "message": "Character not found"}), 404
    except Exception as e:
        app.logger.error(
            f"{Fore.RED}Error saving current character: {e}{Style.RESET_ALL}"
        )
        return jsonify(
            {"status": "error", "message": "Error saving current character."}
        ), 500


@app.route("/game_preferences")
def game_preferences():
    try:
        user_id = "default_user"
        # Fetch preferences from the database
        preferences = GamePreferences.query.filter_by(user_id=user_id).first()

        preferences_data = {
            "gameStyle": preferences.game_style if preferences else "",
            "tone": preferences.tone if preferences else "",
            "difficulty": preferences.difficulty if preferences else "",
            "theme": preferences.theme if preferences else "",
        }

        # Save the preferences in the session
        session["user_preferences"] = preferences_data
        session.modified = True

        app.logger.debug(
            f"{Fore.MAGENTA}Game preferences loaded and stored in session: {preferences_data}{Style.RESET_ALL}"
        )

        return render_template("game_preferences.html", preferences=preferences_data)
    except Exception as e:
        app.logger.error(
            f"{Fore.RED}Error loading game preferences: {e}{Style.RESET_ALL}"
        )
        return jsonify(
            {"status": "error", "message": "Error loading game preferences."}
        ), 500


@app.route("/submit_preferences", methods=["POST"])
def submit_preferences():
    try:
        preferences_data = request.json.get("preferences", {})
        user_id = "default_user"

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

        # Check if preferences already exist for this user
        existing_preferences = GamePreferences.query.filter_by(user_id=user_id).first()

        if existing_preferences:
            # Update the existing preferences
            existing_preferences.game_style = preferences_data["gameStyle"]
            existing_preferences.tone = preferences_data["tone"]
            existing_preferences.difficulty = preferences_data["difficulty"]
            existing_preferences.theme = preferences_data["theme"]
        else:
            # Create new preferences
            new_preferences = GamePreferences(
                user_id=user_id,
                game_style=preferences_data["gameStyle"],
                tone=preferences_data["tone"],
                difficulty=preferences_data["difficulty"],
                theme=preferences_data["theme"],
            )
            db.session.add(new_preferences)

        db.session.commit()

        return jsonify({"message": "Preferences saved successfully!"})
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"{Fore.RED}Error submitting preferences: {e}{Style.RESET_ALL}"
        )
        return jsonify({"status": "error", "message": "Error saving preferences."}), 500


@app.route("/save_game", methods=["POST"])
def save_game():
    try:
        # Check Content-Type header
        if not request.is_json:
            return jsonify(
                {
                    "status": "error",
                    "message": "Invalid Content-Type, expecting application/json",
                }
            ), 415

        # Retrieve game data from session
        conversation_history = session.get("conversation_history", [])
        storyline = session.get("storyline", "")
        current_character = session.get("current_character", None)

        if not current_character:
            return jsonify(
                {"status": "error", "message": "No character selected!"}
            ), 400

        game_name = request.json.get("game_name", "").strip()
        if not game_name:
            return jsonify(
                {"status": "error", "message": "Game name cannot be empty!"}
            ), 400

        user_id = "default_user"  # Replace with actual user ID if applicable
        existing_game = SavedGame.query.filter_by(
            user_id=user_id, game_name=game_name
        ).first()

        if existing_game:
            # Overwrite existing game
            existing_game.conversation_history = json.dumps(conversation_history)
            existing_game.storyline = storyline
            existing_game.character_id = current_character["id"]
            db.session.commit()
            return jsonify(
                {
                    "status": "success",
                    "message": f'Game "{game_name}" updated successfully!',
                }
            ), 200

        # Save new game to database
        new_saved_game = SavedGame(
            game_name=game_name,
            user_id=user_id,
            conversation_history=json.dumps(conversation_history),
            storyline=storyline,
            character_id=current_character["id"],
        )
        db.session.add(new_saved_game)
        db.session.commit()

        return jsonify(
            {"status": "success", "message": f'Game "{game_name}" saved successfully!'}
        ), 201
    except Exception as e:
        app.logger.error(f"Error saving game: {e}")
        return jsonify({"status": "error", "message": "Error saving game."}), 500


@app.route("/load_game/<int:game_id>", methods=["POST"])
def load_game(game_id):
    try:
        saved_game = db.session.get(SavedGame, game_id)

        if not saved_game:
            return jsonify({"status": "error", "message": "Saved game not found"}), 404

        # Load game data into session
        session["conversation_history"] = json.loads(saved_game.conversation_history)
        session["storyline"] = saved_game.storyline

        character = db.session.get(Character, saved_game.character_id)
        if character:
            session["current_character"] = {
                "id": character.id,
                "name": character.name,
                "race": character.race.name,
                "class": character.character_class.name,
                "background": character.background.name,
                "level": character.level,
                "experience_points": character.experience_points,
                "strength": character.strength,
                "dexterity": character.dexterity,
                "constitution": character.constitution,
                "intelligence": character.intelligence,
                "wisdom": character.wisdom,
                "charisma": character.charisma,
                "max_hit_points": character.max_hit_points,
                "current_hit_points": character.current_hit_points,
                "armor_class": character.armor_class,
                "speed": character.speed,
            }
        session.modified = True

        return jsonify({"status": "success", "message": "Game loaded successfully!"})
    except Exception as e:
        app.logger.error(f"Error loading game: {e}")
        return jsonify({"status": "error", "message": "Error loading game."}), 500


@app.route("/delete_game/<int:game_id>", methods=["DELETE"])
def delete_game(game_id):
    try:
        saved_game = db.session.get(SavedGame, game_id)

        if not saved_game:
            return jsonify({"status": "error", "message": "Game not found"}), 404

        # Proceed to delete the saved game
        db.session.delete(saved_game)
        db.session.commit()

        return jsonify({"status": "success", "message": "Game deleted successfully!"})
    except Exception as e:
        app.logger.error(f"Error deleting game: {e}")
        return jsonify({"status": "error", "message": "Error deleting game."}), 500


@app.route("/check_game_exists/<string:game_name>", methods=["GET"])
def check_game_exists(game_name):
    user_id = "default_user"  # Replace with actual user authentication if needed
    existing_game = SavedGame.query.filter_by(
        user_id=user_id, game_name=game_name
    ).first()

    if existing_game:
        return jsonify({"exists": True})
    return jsonify({"exists": False})


@app.route("/manage_games")
def manage_games():
    try:
        user_id = "default_user"  # Replace with actual user ID if applicable
        saved_games = SavedGame.query.filter_by(user_id=user_id).all()

        return render_template("manage_games.html", saved_games=saved_games)
    except Exception as e:
        app.logger.error(f"Error managing games: {e}")
        return jsonify({"status": "error", "message": "Error managing games."}), 500


@app.route("/thank_you")
def thank_you():
    return render_template("thank_you.html")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    with app.app_context():
        # Check if character data is already populated
        if (
            not Race.query.first()
            or not Class.query.first()
            or not Background.query.first()
        ):
            app.logger.info(
                f"{Fore.GREEN}Character database empty, populating with defaults...{Style.RESET_ALL}"
            )
            populate_character_defaults()
        else:
            app.logger.info(
                f"{Fore.GREEN}Character database already populated, skipping defaults.{Style.RESET_ALL}"
            )

        # Check if game preferences data is already populated
        if not GamePreferences.query.first():
            app.logger.info(
                f"{Fore.GREEN}Game preferences database empty, populating with defaults...{Style.RESET_ALL}"
            )
            populate_game_defaults()
        else:
            app.logger.info(
                f"{Fore.GREEN}Game preferences database already populated, skipping defaults.{Style.RESET_ALL}"
            )

    # Start the Flask application
    app.run(debug=True)
