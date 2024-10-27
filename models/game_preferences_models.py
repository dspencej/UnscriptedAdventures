# models/game_preferences_models.py
from models.character_models import db


class GamePreferences(db.Model):
    __tablename__ = "game_preferences"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)  # Assuming you use a user system
    game_style = db.Column(db.String, nullable=False)
    tone = db.Column(db.String, nullable=False)
    difficulty = db.Column(db.String, nullable=False)
    theme = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<GamePreferences {self.user_id} - {self.game_style}>"


def populate_defaults():
    """Populate the database with default game preferences."""
    # Default preferences for a "default_user"
    default_preferences = [
        {
            "user_id": "default_user",
            "game_style": "narrative",
            "tone": "lighthearted",
            "difficulty": "medium",
            "theme": "fantasy",
        },
        {
            "user_id": "user2",
            "game_style": "combat",
            "tone": "serious",
            "difficulty": "hard",
            "theme": "sci-fi",
        },
        # Add more default preferences here if needed
    ]

    # Iterate through the default preferences and insert them into the database
    for pref in default_preferences:
        # Check if the user_id already exists
        existing_pref = GamePreferences.query.filter_by(user_id=pref["user_id"]).first()
        if not existing_pref:
            # Create new preference entry if it doesn't exist
            new_pref = GamePreferences(
                user_id=pref["user_id"],
                game_style=pref["game_style"],
                tone=pref["tone"],
                difficulty=pref["difficulty"],
                theme=pref["theme"],
            )
            db.session.add(new_pref)

    # Commit the changes to the database
    db.session.commit()
