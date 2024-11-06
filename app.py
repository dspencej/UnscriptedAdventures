import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import ORM models
from llm.llm_agent import generate_gm_response
from llm.llm_config import get_llm_config
from llm.agents import get_agents
from models.character_models import Background, Character, Class, Race
from models.character_models import populate_defaults as populate_character_defaults
from models.game_preferences_models import GamePreferences
from models.game_preferences_models import populate_defaults as populate_game_defaults
from models.save_game_models import SavedGame

# Initialize SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

app = FastAPI()

# Secret key for session management
app_secret_key = os.getenv("SECRET_KEY", "default_secret_key")
app.add_middleware(SessionMiddleware, secret_key=app_secret_key)

# Set up static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database configuration
basedir = Path(__file__).resolve().parent
db_file = basedir / "characters.db"
database_url = f"sqlite:///{db_file}"


engine = create_engine(database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency for database session
def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    request.session.setdefault("conversation_history", [])
    request.session.setdefault("current_character", None)

    current_character = request.session.get("current_character")
    conversation_history = request.session.get("conversation_history")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_character": current_character,
            "conversation_history": conversation_history,
        },
    )


# app.py (continued)


@app.post("/interact")
async def interact(request: Request):
    data = await request.json()
    user_input = data.get("user_input", "").strip()
    user_preferences = request.session.get("user_preferences", {})
    conversation_history = request.session.get("conversation_history", [])
    storyline = request.session.get("storyline", "")
    current_character = request.session.get("current_character", {})

    if not user_input:
        return JSONResponse({"status": "error", "message": "Input cannot be empty!"}, status_code=400)
    if not user_preferences:
        return JSONResponse({"status": "error", "message": "Game preferences not set!"}, status_code=400)
    if not current_character:
        return JSONResponse({"status": "error", "message": "Please load a character!"}, status_code=400)

    # Retrieve LLM configuration from session
    provider = request.session.get("llm_provider", "openai")
    model = request.session.get("llm_model", "gpt-4")  # Adjust default model as needed
    try:
        # Get the unified LLM configuration
        llm_config = get_llm_config(provider)
    except (EnvironmentError, ValueError) as e:
        logger.error(f"LLM Configuration Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    # Create agent instances with the fetched configurations
    agents = get_agents(llm_config)
    dm_agent = agents.get("DMAgent")
    storyteller_agent = agents.get("StorytellerAgent")

    if not dm_agent or not storyteller_agent:
        logger.error("Failed to initialize agents.")
        return JSONResponse({"status": "error", "message": "Failed to initialize agents."}, status_code=500)

    # Pass the agents to the LLM agent
    gm_response = await generate_gm_response(
        user_input,
        conversation_history,
        user_preferences,
        storyline,
        current_character,
        agents=agents  # Pass the agents dictionary
    )

    gm_response_text = gm_response.get("dm_response", "Unknown response") if isinstance(gm_response, dict) else "Unknown response"

    # Update conversation_history
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "gm", "content": gm_response_text})
    request.session["conversation_history"] = conversation_history

    # Update storyline
    storyline = gm_response.get("full_storyline", storyline)
    request.session["storyline"] = storyline  # Reassign to session

    return JSONResponse({"gm_response": gm_response_text})


@app.post("/new_game")
async def new_game(request: Request):
    request.session["conversation_history"] = []
    request.session["user_preferences"] = {}
    request.session["current_character"] = {}
    request.session["storyline"] = ""

    return JSONResponse({"message": "New game started."})


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.post("/submit_contact")
async def submit_contact(name: str = Form(...), email: str = Form(...), message: str = Form(...)):
    logger.info(f"Contact form submitted.\nName: {name}, Email: {email}\nMessage: {message}")
    return RedirectResponse(url="/thank_you", status_code=303)


@app.get("/character_creation", response_class=HTMLResponse)
async def character_creation(request: Request, db: Session = Depends(get_db)):
    races = db.query(Race).all()
    classes = db.query(Class).all()
    backgrounds = db.query(Background).all()
    return templates.TemplateResponse(
        "character_creation.html",
        {"request": request, "races": races, "classes": classes, "backgrounds": backgrounds}
    )


@app.post("/save_character")
async def save_character(request: Request, db: Session = Depends(get_db)):
    character_data = await request.json()
    required_fields = ["name", "race", "class", "background"]
    if not all(character_data.get(field) for field in required_fields):
        return JSONResponse({"message": "All fields are required!"}, status_code=400)

    race = db.query(Race).filter_by(name=character_data["race"]).first()
    character_class = db.query(Class).filter_by(name=character_data["class"]).first()
    background = db.query(Background).filter_by(name=character_data["background"]).first()

    if not race or not character_class or not background:
        return JSONResponse({"message": "Invalid race, class, or background."}, status_code=400)

    new_character = Character(
        name=character_data["name"],
        race=race,
        background=background,
        character_class=character_class,
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

    db.add(new_character)
    db.commit()

    request.session["current_character"] = {
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

    return JSONResponse({"message": "Character saved successfully!"}, status_code=201)


@app.get("/manage_characters", response_class=HTMLResponse)
async def manage_characters(request: Request, db: Session = Depends(get_db)):
    characters = db.query(Character).all()
    return templates.TemplateResponse("manage_characters.html", {"request": request, "characters": characters})


@app.get("/select_character/{character_id}")
async def select_character(character_id: int, request: Request, db: Session = Depends(get_db)):
    character = db.query(Character).get(character_id)
    if not character:
        return JSONResponse({"status": "error", "message": "Character not found"}, status_code=404)

    selected_character = {
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
    request.session["current_character"] = selected_character

    return JSONResponse({"status": "success", "message": f"Character '{character.name}' loaded successfully", "character": selected_character})


@app.post("/delete_character/{character_id}")
async def delete_character(character_id: int, request: Request, db: Session = Depends(get_db)):
    character = db.query(Character).get(character_id)
    if not character:
        return JSONResponse({"status": "error", "message": "Character not found"}, status_code=404)

    db.delete(character)
    db.commit()

    if request.session.get("current_character", {}).get("id") == character_id:
        request.session.pop("current_character", None)

    return JSONResponse({"status": "success", "message": f"Character {character.name} deleted successfully!"})


@app.get("/game_preferences", response_class=HTMLResponse)
async def game_preferences(request: Request, db: Session = Depends(get_db)):
    user_id = "default_user"
    preferences = db.query(GamePreferences).filter_by(user_id=user_id).first()

    preferences_data = {
        "gameStyle": preferences.game_style if preferences else "",
        "tone": preferences.tone if preferences else "",
        "difficulty": preferences.difficulty if preferences else "",
        "theme": preferences.theme if preferences else "",
    }

    request.session["user_preferences"] = preferences_data

    return templates.TemplateResponse("game_preferences.html", {"request": request, "preferences": preferences_data})


@app.post("/submit_preferences")
async def submit_preferences(request: Request, db: Session = Depends(get_db)):
    preferences_data = await request.json()
    user_id = "default_user"

    if not all(preferences_data.get(key) for key in ["gameStyle", "tone", "difficulty", "theme"]):
        return JSONResponse({"message": "All preferences are required!"}, status_code=400)

    existing_preferences = db.query(GamePreferences).filter_by(user_id=user_id).first()
    if existing_preferences:
        existing_preferences.game_style = preferences_data["gameStyle"]
        existing_preferences.tone = preferences_data["tone"]
        existing_preferences.difficulty = preferences_data["difficulty"]
        existing_preferences.theme = preferences_data["theme"]
    else:
        new_preferences = GamePreferences(user_id=user_id, **preferences_data)
        db.add(new_preferences)

    db.commit()
    return JSONResponse({"message": "Preferences saved successfully!"})


@app.post("/save_game")
async def save_game(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    game_name = data.get("game_name", "").strip()
    user_id = "default_user"

    conversation_history = request.session.get("conversation_history", [])
    storyline = request.session.get("storyline", "")
    current_character = request.session.get("current_character")

    if not current_character:
        return JSONResponse({"status": "error", "message": "No character selected!"}, status_code=400)
    if not game_name:
        return JSONResponse({"status": "error", "message": "Game name cannot be empty!"}, status_code=400)

    existing_game = db.query(SavedGame).filter_by(user_id=user_id, game_name=game_name).first()
    if existing_game:
        existing_game.conversation_history = json.dumps(conversation_history)
        existing_game.storyline = storyline
        existing_game.character_id = current_character["id"]
    else:
        new_game = SavedGame(
            game_name=game_name,
            user_id=user_id,
            conversation_history=json.dumps(conversation_history),
            storyline=storyline,
            character_id=current_character["id"],
        )
        db.add(new_game)
    db.commit()

    return JSONResponse({"status": "success", "message": f'Game "{game_name}" saved successfully!'})


@app.post("/load_game/{game_id}")
async def load_game(game_id: int, request: Request, db: Session = Depends(get_db)):
    saved_game = db.query(SavedGame).get(game_id)
    if not saved_game:
        return JSONResponse({"status": "error", "message": "Saved game not found"}, status_code=404)

    # Load game data into session
    request.session["conversation_history"] = json.loads(saved_game.conversation_history)
    request.session["storyline"] = saved_game.storyline

    character = db.query(Character).get(saved_game.character_id)
    if character:
        request.session["current_character"] = {
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

    return JSONResponse({"status": "success", "message": "Game loaded successfully!"})


@app.delete("/delete_character/{character_id}")
async def delete_character(character_id: int, request: Request, db: Session = Depends(get_db)):
    character = db.query(Character).get(character_id)
    if not character:
        return JSONResponse({"status": "error", "message": "Character not found"}, status_code=404)

    db.delete(character)
    db.commit()

    # Remove character from session if it's the current one
    if request.session.get("current_character", {}).get("id") == character_id:
        request.session.pop("current_character", None)

    return JSONResponse({"status": "success", "message": f"Character {character.name} deleted successfully!"})


@app.delete("/delete_game/{game_id}")
async def delete_game(game_id: int, db: Session = Depends(get_db)):
    saved_game = db.query(SavedGame).get(game_id)
    if not saved_game:
        return JSONResponse({"status": "error", "message": "Game not found"}, status_code=404)

    db.delete(saved_game)
    db.commit()
    return JSONResponse({"status": "success", "message": "Game deleted successfully!"})


@app.get("/check_game_exists/{game_name}")
async def check_game_exists(game_name: str, db: Session = Depends(get_db)):
    user_id = "default_user"
    exists = db.query(SavedGame).filter_by(user_id=user_id, game_name=game_name).first() is not None
    return JSONResponse({"exists": exists})


@app.get("/check_character_name/{name}")
async def check_character_name(name: str, db: Session = Depends(get_db)):
    existing_character = db.query(Character).filter_by(name=name).first()
    if existing_character:
        return {"exists": True}
    return {"exists": False}


@app.get("/manage_games", response_class=HTMLResponse)
async def manage_games(request: Request, db: Session = Depends(get_db)):
    user_id = "default_user"
    saved_games = db.query(SavedGame).filter_by(user_id=user_id).all()
    return templates.TemplateResponse("manage_games.html", {"request": request, "saved_games": saved_games})


@app.get("/thank_you", response_class=HTMLResponse)
async def thank_you(request: Request):
    return templates.TemplateResponse("thank_you.html", {"request": request})


@app.get("/llm_config", response_class=HTMLResponse)
async def llm_config(request: Request):
    # Retrieve current selections from session, if any
    current_provider = request.session.get("llm_provider", "openai")
    current_model = request.session.get("llm_model", "gpt-3.5-turbo")
    return templates.TemplateResponse(
        "llm_config.html",
        {
            "request": request,
            "current_provider": current_provider,
            "current_model": current_model
        }
    )


@app.post("/llm_config", response_class=HTMLResponse)
async def post_llm_config(request: Request):
    # Parse JSON data from request body
    form_data = await request.json()
    provider = form_data.get("provider")
    model = form_data.get("model")

    # Validate provider and model
    valid_providers = ["openai", "ollama"]
    valid_models = {
        "openai": ["gpt-3.5-turbo", "gpt-4"],
        "ollama": ["llama3:latest"]
    }

    if provider not in valid_providers:
        return JSONResponse({"status": "error", "message": "Invalid provider selected."}, status_code=400)

    if model not in valid_models.get(provider, []):
        return JSONResponse({"status": "error", "message": "Invalid model selected for the provider."}, status_code=400)

    # Store selections in session
    request.session["llm_provider"] = provider
    request.session["llm_model"] = model

    # Return a success response
    return JSONResponse({"status": "success", "message": "LLM Configuration has been saved successfully!"})


if __name__ == "__main__":
    import uvicorn

    with engine.begin() as conn:
        if not engine.dialect.has_table(conn, "race"):
            populate_character_defaults()
        if not engine.dialect.has_table(conn, "game_preferences"):
            populate_game_defaults()

    uvicorn.run("app:app", host="127.0.0.1", port=8000, log_level="info")
