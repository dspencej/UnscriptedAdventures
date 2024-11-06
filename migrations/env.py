# migrations/env.py

import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Include your project's root directory in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your Base and models here
from db.database import Base
from models.character_models import Character, Race, Class, Background
from models.game_preferences_models import GamePreferences
from models.save_game_models import SavedGame, ConversationPair
from models.user_models import User  # Import the User model

# this is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Set the database URL from your application settings or environment variable
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///characters.db')  # Adjust the path if needed
config.set_main_option('sqlalchemy.url', DATABASE_URL)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True  # Necessary for SQLite migrations
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
