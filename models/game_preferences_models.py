# models/game_preferences_models.py

from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy.types import Enum as SQLEnum

from db.database import Base  # Import Base from your database module


# Enums for controlled attributes
class GameStyleEnum(Enum):
    NARRATIVE = "narrative"
    COMBAT = "combat"
    EXPLORATION = "exploration"
    MIXED = "mixed"


class ToneEnum(Enum):
    LIGHTHEARTED = "lighthearted"
    SERIOUS = "serious"
    DARK = "dark"
    HUMOROUS = "humorous"


class DifficultyEnum(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class ThemeEnum(Enum):
    FANTASY = "fantasy"
    SCIFI = "sci-fi"
    HORROR = "horror"
    MODERN = "modern"
    HISTORICAL = "historical"


class GamePreferences(Base):
    __tablename__ = "game_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True
    )  # Changed to Integer to match User model
    game_style = Column(SQLEnum(GameStyleEnum), nullable=False)
    tone = Column(SQLEnum(ToneEnum), nullable=False)
    difficulty = Column(SQLEnum(DifficultyEnum), nullable=False)
    theme = Column(SQLEnum(ThemeEnum), nullable=False)

    user = relationship("User", backref="game_preferences")

    def __repr__(self):
        return f"<GamePreferences {self.user_id} - {self.game_style.value}>"

    @validates("game_style")
    def validate_game_style(self, key, value):
        if not isinstance(value, GameStyleEnum):
            raise ValueError(f"Invalid game style: {value}")
        return value

    @validates("tone")
    def validate_tone(self, key, value):
        if not isinstance(value, ToneEnum):
            raise ValueError(f"Invalid tone: {value}")
        return value

    @validates("difficulty")
    def validate_difficulty(self, key, value):
        if not isinstance(value, DifficultyEnum):
            raise ValueError(f"Invalid difficulty: {value}")
        return value

    @validates("theme")
    def validate_theme(self, key, value):
        if not isinstance(value, ThemeEnum):
            raise ValueError(f"Invalid theme: {value}")
        return value


def populate_defaults(session):
    """Populate the database with default game preferences."""
    default_preferences = [
        {
            "user_id": "default_user",
            "game_style": GameStyleEnum.NARRATIVE,
            "tone": ToneEnum.LIGHTHEARTED,
            "difficulty": DifficultyEnum.MEDIUM,
            "theme": ThemeEnum.FANTASY,
        },
        {
            "user_id": "user2",
            "game_style": GameStyleEnum.COMBAT,
            "tone": ToneEnum.SERIOUS,
            "difficulty": DifficultyEnum.HARD,
            "theme": ThemeEnum.SCIFI,
        },
        {
            "user_id": "user3",
            "game_style": GameStyleEnum.EXPLORATION,
            "tone": ToneEnum.HUMOROUS,
            "difficulty": DifficultyEnum.EASY,
            "theme": ThemeEnum.MODERN,
        },
        {
            "user_id": "user4",
            "game_style": GameStyleEnum.MIXED,
            "tone": ToneEnum.DARK,
            "difficulty": DifficultyEnum.EXPERT,
            "theme": ThemeEnum.HORROR,
        },
    ]

    for pref in default_preferences:
        existing_pref = (
            session.query(GamePreferences).filter_by(user_id=pref["user_id"]).first()
        )
        if not existing_pref:
            new_pref = GamePreferences(
                user_id=pref["user_id"],
                game_style=pref["game_style"],
                tone=pref["tone"],
                difficulty=pref["difficulty"],
                theme=pref["theme"],
            )
            session.add(new_pref)
    session.commit()
