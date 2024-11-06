from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    func,
    UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from db.database import Base  # Import Base from your database module

class SavedGame(Base):
    __tablename__ = 'saved_games'
    __table_args__ = (
        UniqueConstraint('user_id', 'game_name', name='uq_user_game'),
    )

    id = Column(Integer, primary_key=True)
    game_name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    save_time = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", backref="saved_games")
    character = relationship("Character", backref="saved_games")
    conversation_pairs = relationship(
        "ConversationPair",
        back_populates="game",
        cascade="all, delete-orphan",
        order_by="ConversationPair.order"
    )

    @validates('game_name')
    def validate_game_name(self, key, value):
        if not value or not value.strip():
            raise ValueError("Game name cannot be empty")
        return value.strip()

    def __repr__(self):
        return f"<SavedGame {self.game_name} for User {self.user_id}>"

class ConversationPair(Base):
    __tablename__ = 'conversation_pairs'
    __table_args__ = (
        UniqueConstraint('game_id', 'order', name='uq_game_order'),
    )

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('saved_games.id'), nullable=False)
    order = Column(Integer, nullable=False)
    user_input = Column(Text, nullable=False)
    gm_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    game = relationship("SavedGame", back_populates="conversation_pairs")

    @validates('order')
    def validate_order(self, key, value):
        if value is None or value <= 0:
            raise ValueError("Order must be a positive integer")
        return value

    @validates('user_input', 'gm_response')
    def validate_text_fields(self, key, value):
        if not value or not value.strip():
            raise ValueError(f"{key.replace('_', ' ').capitalize()} cannot be empty")
        return value.strip()

    def __repr__(self):
        return f"<ConversationPair {self.order} for Game ID {self.game_id}>"
