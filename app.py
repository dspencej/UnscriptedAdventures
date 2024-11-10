# app.py

import os
import datetime
import logging

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import ORM models and database utilities
from llm.llm_agent import generate_gm_response
from llm.llm_config import get_llm_config
from llm.agents import get_agents
from models.character_models import Background, Character, Class, Race
from models.character_models import populate_defaults as populate_character_defaults
from models.game_preferences_models import (
    GamePreferences,
    GameStyleEnum,
    ToneEnum,
    DifficultyEnum,
    ThemeEnum,
)
from models.game_preferences_models import populate_defaults as populate_game_defaults
from models.save_game_models import SavedGame, ConversationPair
from models.user_models import User
from db.database import engine, SessionLocal, Base

# Load environment variables
load_dotenv()

app = FastAPI()

# Secret key for session management
app_secret_key = os.getenv("SECRET_KEY", "default_secret_key")
app.add_middleware(SessionMiddleware, secret_key=app_secret_key)  # type: ignore

# Set up static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Dependency for database session
def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


# Dependency to get the current user (simplified for this example)
def get_current_user(db: Session = Depends(get_db)):
    # In a real application, you would retrieve the user from the session or token
    user = db.query(User).filter_by(username="default_user").first()
    return user


# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]")
logger = logging.getLogger(__name__)

# Initialize the database and create tables if they do not exist
with engine.begin() as conn:
    Base.metadata.create_all(bind=engine)  # Create all tables if not already created
    with SessionLocal() as session:
        populate_character_defaults(session)  # Pass the session
        populate_game_defaults(session)

        # Create a default user if not exists
        default_user = session.query(User).filter_by(username="default_user").first()
        if not default_user:
            default_user = User(
                username="default_user", email="default_user@example.com"
            )
            session.add(default_user)
            session.commit()


# Application Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    request.session.setdefault("current_character", None)
    saved_game_id = request.session.get("saved_game_id")

    conversation_history = []
    if saved_game_id:
        # Retrieve conversation history from the database
        conversation_pairs = (
            db.query(ConversationPair)
            .filter_by(game_id=saved_game_id)
            .order_by(ConversationPair.order)
            .all()
        )
        conversation_history = []
        for pair in conversation_pairs:
            if pair.user_input:
                conversation_history.append(
                    {"role": "user", "content": pair.user_input}
                )
            if pair.gm_response:
                conversation_history.append({"role": "gm", "content": pair.gm_response})

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_character": request.session.get("current_character"),
            "conversation_history": conversation_history,
        },
    )


@app.post("/interact")
async def interact(
    request: Request,
    db: Session = Depends(get_db),
):
    data = await request.json()
    user_input = data.get("user_input", "").strip()
    user_preferences = request.session.get("user_preferences", {})
    current_character = request.session.get("current_character", {})
    saved_game_id = request.session.get("saved_game_id")

    if not user_input:
        return JSONResponse(
            {"status": "error", "message": "Input cannot be empty!"}, status_code=400
        )
    if not user_preferences:
        return JSONResponse(
            {"status": "error", "message": "Game preferences not set!"}, status_code=400
        )
    if not current_character:
        return JSONResponse(
            {"status": "error", "message": "Please load a character!"}, status_code=400
        )
    if not saved_game_id:
        return JSONResponse(
            {"status": "error", "message": "No game started! Please start a new game."},
            status_code=400,
        )

    # Retrieve LLM configuration from session
    provider = request.session.get("llm_provider", "openai")
    model = request.session.get("llm_model", "gpt-4")
    try:
        # Get the unified LLM configuration
        llm_config = get_llm_config(provider, model)  # noqa
    except (EnvironmentError, ValueError) as e:
        logger.error(f"LLM Configuration Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    # Create agent instances with the fetched configurations
    agents = get_agents(llm_config)
    dm_agent = agents.get("DMAgent")
    storyteller_agent = agents.get("StorytellerAgent")

    if not dm_agent or not storyteller_agent:
        logger.error("Failed to initialize agents.")
        return JSONResponse(
            {"status": "error", "message": "Failed to initialize agents."},
            status_code=500,
        )

    # Call the GM response generator with the saved_game_id and database session
    gm_response = await generate_gm_response(
        user_input=user_input,
        user_preferences=user_preferences,
        current_character=current_character,
        agents=agents,
        saved_game_id=saved_game_id,
        db=db,
    )

    gm_response_text = (
        gm_response.get("response", "Unknown response")
        if isinstance(gm_response, dict)
        else "Unknown response"
    )

    return JSONResponse({"gm_response": gm_response_text})


# Modify the /new_game route
@app.post("/new_game")
async def new_game(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    current_character = request.session.get("current_character")

    if not current_character:
        return JSONResponse(
            {
                "status": "error",
                "message": "Please select a character before starting a new game.",
            },
            status_code=400,
        )

    # Create a new SavedGame instance
    new_game = SavedGame(  # noqa
        game_name=f"{current_character['name']} - {datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}",
        user_id=user.id,
        character_id=current_character["id"],
    )
    db.add(new_game)
    db.commit()
    db.refresh(new_game)  # Refresh to get the new game ID

    # Store saved_game_id in session
    request.session["saved_game_id"] = new_game.id
    logger.info(f"New game started with ID: {new_game.id} and saved to session.")

    # Confirm session saved the ID correctly
    if (
        "saved_game_id" not in request.session
        or request.session["saved_game_id"] != new_game.id
    ):
        logger.error("Failed to store 'saved_game_id' in the session.")
        return JSONResponse(
            {
                "status": "error",
                "message": "Failed to start the new game due to session error.",
            },
            status_code=500,
        )

    return JSONResponse({"message": "New game started.", "saved_game_id": new_game.id})


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.post("/submit_contact")
async def submit_contact(
    name: str = Form(...), email: str = Form(...), message: str = Form(...)
):
    logger.info(
        f"Contact form submitted.\nName: {name}, Email: {email}\nMessage: {message}"
    )
    return RedirectResponse(url="/thank_you", status_code=303)


@app.get("/character_creation", response_class=HTMLResponse)
async def character_creation(request: Request, db: Session = Depends(get_db)):
    races = db.query(Race).all()
    classes = db.query(Class).all()
    backgrounds = db.query(Background).all()
    return templates.TemplateResponse(
        "character_creation.html",
        {
            "request": request,
            "races": races,
            "classes": classes,
            "backgrounds": backgrounds,
        },
    )


@app.post("/save_character")
async def save_character(request: Request, db: Session = Depends(get_db)):
    character_data = await request.json()
    required_fields = ["name", "race", "class", "background"]
    if not all(character_data.get(field) for field in required_fields):
        return JSONResponse({"message": "All fields are required!"}, status_code=400)

    race = db.query(Race).filter_by(name=character_data["race"]).first()
    character_class = db.query(Class).filter_by(name=character_data["class"]).first()
    background = (
        db.query(Background).filter_by(name=character_data["background"]).first()
    )

    if not race or not character_class or not background:
        return JSONResponse(
            {"message": "Invalid race, class, or background."}, status_code=400
        )

    new_character = Character(
        name=character_data["name"],
        race_id=race.id,
        background_id=background.id,
        class_id=character_class.id,
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
    return templates.TemplateResponse(
        "manage_characters.html", {"request": request, "characters": characters}
    )


@app.get("/select_character/{character_id}")
async def select_character(
    character_id: int, request: Request, db: Session = Depends(get_db)
):
    character = db.query(Character).get(character_id)
    if not character:
        return JSONResponse(
            {"status": "error", "message": "Character not found"}, status_code=404
        )

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

    return JSONResponse(
        {
            "status": "success",
            "message": f"Character '{character.name}' loaded successfully",
            "character": selected_character,
        }
    )


@app.post("/delete_character/{character_id}")
async def delete_character(
    character_id: int, request: Request, db: Session = Depends(get_db)
):
    character = db.query(Character).get(character_id)
    if not character:
        return JSONResponse(
            {"status": "error", "message": "Character not found"}, status_code=404
        )

    db.delete(character)
    db.commit()

    # Remove character from session if it's the current one
    if request.session.get("current_character", {}).get("id") == character_id:
        request.session.pop("current_character", None)

    return JSONResponse(
        {
            "status": "success",
            "message": f"Character {character.name} deleted successfully!",
        }
    )


@app.get("/game_preferences", response_class=HTMLResponse)
async def game_preferences(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    preferences = db.query(GamePreferences).filter_by(user_id=user.id).first()

    preferences_data = {
        "gameStyle": preferences.game_style.value if preferences else "",
        "tone": preferences.tone.value if preferences else "",
        "difficulty": preferences.difficulty.value if preferences else "",
        "theme": preferences.theme.value if preferences else "",
    }

    request.session["user_preferences"] = preferences_data

    return templates.TemplateResponse(
        "game_preferences.html", {"request": request, "preferences": preferences_data}
    )


@app.post("/submit_preferences")
async def submit_preferences(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    preferences_data = await request.json()

    if not all(
        preferences_data.get(key)
        for key in ["gameStyle", "tone", "difficulty", "theme"]
    ):
        return JSONResponse(
            {"message": "All preferences are required!"}, status_code=400
        )

    # Convert strings to Enums
    try:
        preferences_data_enum = {
            "game_style": GameStyleEnum(preferences_data["gameStyle"]),
            "tone": ToneEnum(preferences_data["tone"]),
            "difficulty": DifficultyEnum(preferences_data["difficulty"]),
            "theme": ThemeEnum(preferences_data["theme"]),
        }
    except ValueError as e:
        return JSONResponse(
            {"message": f"Invalid preference value: {e}"}, status_code=400
        )

    existing_preferences = db.query(GamePreferences).filter_by(user_id=user.id).first()
    if existing_preferences:
        existing_preferences.game_style = preferences_data_enum["game_style"]
        existing_preferences.tone = preferences_data_enum["tone"]
        existing_preferences.difficulty = preferences_data_enum["difficulty"]
        existing_preferences.theme = preferences_data_enum["theme"]
    else:
        new_preferences = GamePreferences(user_id=user.id, **preferences_data_enum)
        db.add(new_preferences)

    db.commit()
    return JSONResponse({"message": "Preferences saved successfully!"})


@app.post("/load_game/{game_id}")
async def load_game(
    game_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    saved_game = db.query(SavedGame).filter_by(id=game_id, user_id=user.id).first()
    if not saved_game:
        return JSONResponse(
            {"status": "error", "message": "Saved game not found"}, status_code=404
        )

    # Store saved_game_id in session
    request.session["saved_game_id"] = saved_game.id

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
    else:
        return JSONResponse(
            {
                "status": "error",
                "message": "Character associated with the game not found.",
            },
            status_code=404,
        )

    return JSONResponse(
        {"status": "success", "message": "Game loaded successfully!"}, status_code=200
    )


from fastapi import Query  # noqa: E402


@app.delete("/delete_character/{character_id}")
async def delete_character(  # noqa: F811
    character_id: int,
    request: Request,
    db: Session = Depends(get_db),
    confirm: bool = Query(False),
):
    character = db.query(Character).get(character_id)
    if not character:
        return JSONResponse(
            {"status": "error", "message": "Character not found"}, status_code=404
        )

    # Check if there are saved games associated with this character
    saved_games_count = (
        db.query(SavedGame).filter(SavedGame.character_id == character_id).count()  # type: ignore
    )

    # If there are saved games and confirm is not set, prompt for confirmation
    if saved_games_count > 0 and not confirm:
        return JSONResponse(
            {
                "status": "confirm",
                "message": f"Deleting this character will also delete {saved_games_count} "
                f"associated saved game(s). Please confirm to proceed.",
            }
        )

    # If confirmed, delete saved games and character
    if saved_games_count > 0:
        db.query(SavedGame).filter(SavedGame.character_id == character_id).delete()  # type: ignore

    db.delete(character)
    db.commit()

    # Remove character from session if it's the current one
    if request.session.get("current_character", {}).get("id") == character_id:
        request.session.pop("current_character", None)

    return JSONResponse(
        {
            "status": "success",
            "message": f"Character {character.name} and associated saved games deleted successfully!",
        }
    )


@app.delete("/delete_game/{game_id}")
async def delete_game(
    game_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    saved_game = db.query(SavedGame).filter_by(id=game_id, user_id=user.id).first()
    if not saved_game:
        return JSONResponse(
            {"status": "error", "message": "Game not found"}, status_code=404
        )

    db.delete(saved_game)
    db.commit()
    return JSONResponse(
        {"status": "success", "message": "Game deleted successfully!"}, status_code=200
    )


@app.get("/check_game_exists/{game_name}")
async def check_game_exists(
    game_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exists = (
        db.query(SavedGame).filter_by(user_id=user.id, game_name=game_name).first()
        is not None
    )
    return JSONResponse({"exists": exists}, status_code=200)


@app.get("/check_character_name/{name}")
async def check_character_name(name: str, db: Session = Depends(get_db)):
    existing_character = db.query(Character).filter_by(name=name).first()
    if existing_character:
        return {"exists": True}
    return {"exists": False}


@app.get("/manage_games", response_class=HTMLResponse)
async def manage_games(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    saved_games = db.query(SavedGame).filter_by(user_id=user.id).all()
    return templates.TemplateResponse(
        "manage_games.html", {"request": request, "saved_games": saved_games}
    )


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
            "current_model": current_model,
        },
    )


@app.post("/llm_config", response_class=JSONResponse)
async def post_llm_config(request: Request):
    # Parse JSON data from request body
    form_data = await request.json()
    provider = form_data.get("provider")
    model = form_data.get("model")

    # Validate provider and model
    valid_providers = ["openai", "ollama"]
    valid_models = {
        "openai": ["gpt-3.5-turbo", "gpt-4"],
        "ollama": [
            "llama3:latest",
            "mistral:latest",
            "llama3.2:latest",
            "llama3.1:latest",
        ],
    }

    if provider not in valid_providers:
        return JSONResponse(
            {"status": "error", "message": "Invalid provider selected."},
            status_code=400,
        )

    if model not in valid_models.get(provider, []):
        return JSONResponse(
            {"status": "error", "message": "Invalid model selected for the provider."},
            status_code=400,
        )

    # Store selections in session
    request.session["llm_provider"] = provider
    request.session["llm_model"] = model

    # Return a success response
    return JSONResponse(
        {
            "status": "success",
            "message": "LLM Configuration has been saved successfully!",
        },
        status_code=200,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8001, log_level="info")
