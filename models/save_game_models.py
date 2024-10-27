# models/save_game_models.py
from datetime import datetime

from models.character_models import db


class SavedGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(
        db.String(100), nullable=False
    )  # Replace with actual user ID if applicable
    save_time = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_history = db.Column(db.Text, nullable=False)
    storyline = db.Column(db.Text, nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)

    def __repr__(self):
        return f"<SavedGame {self.game_name} for User {self.user_id}>"
