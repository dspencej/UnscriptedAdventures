# models/character_models.py

from enum import Enum

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates

db = SQLAlchemy()

# Association tables
character_inventory = db.Table(
    "character_inventory",
    db.Column(
        "character_id", db.Integer, db.ForeignKey("characters.id"), primary_key=True
    ),
    db.Column("item_id", db.Integer, db.ForeignKey("items.id"), primary_key=True),
)

character_feats = db.Table(
    "character_feats",
    db.Column(
        "character_id", db.Integer, db.ForeignKey("characters.id"), primary_key=True
    ),
    db.Column("feat_id", db.Integer, db.ForeignKey("feats.id"), primary_key=True),
)

character_features = db.Table(
    "character_features",
    db.Column(
        "character_id", db.Integer, db.ForeignKey("characters.id"), primary_key=True
    ),
    db.Column("feature_id", db.Integer, db.ForeignKey("features.id"), primary_key=True),
)

character_languages = db.Table(
    "character_languages",
    db.Column(
        "character_id", db.Integer, db.ForeignKey("characters.id"), primary_key=True
    ),
    db.Column(
        "language_id", db.Integer, db.ForeignKey("languages.id"), primary_key=True
    ),
)


# Enums
class AlignmentEnum(Enum):
    LG = "Lawful Good"
    NG = "Neutral Good"
    CG = "Chaotic Good"
    LN = "Lawful Neutral"
    N = "Neutral"
    CN = "Chaotic Neutral"
    LE = "Lawful Evil"
    NE = "Neutral Evil"
    CE = "Chaotic Evil"


class Character(db.Model):
    __tablename__ = "characters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    race_id = db.Column(db.Integer, db.ForeignKey("races.id"), nullable=True)
    background_id = db.Column(
        db.Integer, db.ForeignKey("backgrounds.id"), nullable=True
    )
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id"), nullable=False
    )  # Direct relationship to Class
    alignment = db.Column(db.Enum(AlignmentEnum), nullable=True)

    # Core Stats
    level = db.Column(db.Integer, default=1)
    experience_points = db.Column(db.Integer, default=0)

    # Ability Scores
    strength = db.Column(db.Integer, nullable=False)
    dexterity = db.Column(db.Integer, nullable=False)
    constitution = db.Column(db.Integer, nullable=False)
    intelligence = db.Column(db.Integer, nullable=False)
    wisdom = db.Column(db.Integer, nullable=False)
    charisma = db.Column(db.Integer, nullable=False)

    proficiency_bonus = db.Column(db.Integer, default=2)  # Increases with level

    # Combat-related attributes
    max_hit_points = db.Column(db.Integer, nullable=False, default=10)
    current_hit_points = db.Column(db.Integer, nullable=False, default=10)
    temporary_hit_points = db.Column(db.Integer, default=0)
    armor_class = db.Column(db.Integer, nullable=False, default=10)
    initiative = db.Column(db.Integer, default=0)  # Typically Dex modifier
    speed = db.Column(db.Integer, nullable=False, default=30)  # Base walking speed

    # Death saves
    death_saves_successes = db.Column(db.Integer, default=0)
    death_saves_failures = db.Column(db.Integer, default=0)

    # Relationships
    race = db.relationship("Race", backref="characters")
    background = db.relationship("Background", backref="characters")
    character_class = db.relationship(
        "Class", backref="characters"
    )  # Direct single-class relationship
    inventory = db.relationship(
        "Item",
        secondary=character_inventory,
        lazy="subquery",
        backref=db.backref("owners", lazy=True),
    )
    feats = db.relationship(
        "Feat",
        secondary=character_feats,
        lazy="subquery",
        backref=db.backref("characters", lazy=True),
    )
    features = db.relationship(
        "Feature",
        secondary=character_features,
        lazy="subquery",
        backref=db.backref("characters", lazy=True),
    )
    spells = db.relationship("Spell", backref="character", lazy=True)
    languages = db.relationship(
        "Language",
        secondary=character_languages,
        lazy="subquery",
        backref=db.backref("characters", lazy=True),
    )
    conditions = db.relationship("CharacterCondition", backref="character", lazy=True)
    proficiencies = db.relationship("Proficiency", backref="character", lazy=True)

    # Saving Throws
    strength_save = db.Column(db.Boolean, default=False)
    dexterity_save = db.Column(db.Boolean, default=False)
    constitution_save = db.Column(db.Boolean, default=False)
    intelligence_save = db.Column(db.Boolean, default=False)
    wisdom_save = db.Column(db.Boolean, default=False)
    charisma_save = db.Column(db.Boolean, default=False)

    # Ability Modifiers (Computed)
    @property
    def strength_mod(self):
        return (self.strength - 10) // 2

    @property
    def dexterity_mod(self):
        return (self.dexterity - 10) // 2

    @property
    def constitution_mod(self):
        return (self.constitution - 10) // 2

    @property
    def intelligence_mod(self):
        return (self.intelligence - 10) // 2

    @property
    def wisdom_mod(self):
        return (self.wisdom - 10) // 2

    @property
    def charisma_mod(self):
        return (self.charisma - 10) // 2

    # Saving Throws Bonuses
    @property
    def strength_save_bonus(self):
        return self.strength_mod + (self.proficiency_bonus if self.strength_save else 0)

    @property
    def dexterity_save_bonus(self):
        return self.dexterity_mod + (
            self.proficiency_bonus if self.dexterity_save else 0
        )

    @property
    def constitution_save_bonus(self):
        return self.constitution_mod + (
            self.proficiency_bonus if self.constitution_save else 0
        )

    @property
    def intelligence_save_bonus(self):
        return self.intelligence_mod + (
            self.proficiency_bonus if self.intelligence_save else 0
        )

    @property
    def wisdom_save_bonus(self):
        return self.wisdom_mod + (self.proficiency_bonus if self.wisdom_save else 0)

    @property
    def charisma_save_bonus(self):
        return self.charisma_mod + (self.proficiency_bonus if self.charisma_save else 0)

    # Validation for Ability Scores and combat attributes
    @validates(
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
        "max_hit_points",
        "armor_class",
        "speed",
    )
    def validate_scores_and_combat(self, key, value):
        if key in [
            "strength",
            "dexterity",
            "constitution",
            "intelligence",
            "wisdom",
            "charisma",
        ]:
            if not 1 <= value <= 30:
                raise ValueError(f"{key.capitalize()} must be between 1 and 30")
        if value < 0:
            raise ValueError(f"{key.capitalize()} must be greater than or equal to 0")
        return value

    def __repr__(self):
        return f"<Character {self.name} (Level {self.level})>"


class Race(db.Model):
    __tablename__ = "races"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True, index=True)
    ability_increases = db.Column(
        db.JSON
    )  # e.g., { 'dexterity': 2, 'intelligence': 1 }
    size = db.Column(db.String)  # Medium, Small, etc.
    speed = db.Column(db.Integer)
    darkvision = db.Column(db.Boolean, default=False)
    traits = db.Column(db.JSON)  # Racial traits
    subraces = db.relationship("Subrace", backref="race", lazy=True)
    features = db.relationship("Feature", backref="race", lazy=True)

    def __repr__(self):
        return f"<Race {self.name}>"


class Subrace(db.Model):
    __tablename__ = "subraces"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    race_id = db.Column(db.Integer, db.ForeignKey("races.id"))
    ability_increases = db.Column(db.JSON)  # Subrace ability modifiers
    traits = db.Column(db.JSON)  # Subrace-specific traits
    features = db.relationship("Feature", backref="subrace", lazy=True)

    def __repr__(self):
        return f"<Subrace {self.name}>"


class Class(db.Model):
    __tablename__ = "classes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True, index=True)
    hit_die = db.Column(db.Integer)  # d6, d8, etc.
    primary_ability = db.Column(db.String)  # Charisma, Intelligence, etc.
    saving_throw_proficiencies = db.Column(
        db.JSON
    )  # e.g., { 'strength': True, 'dexterity': False }
    proficiencies = db.Column(db.JSON)  # Weapons, armor, tools
    subclass_available = db.Column(db.Boolean, default=True)
    features = db.relationship("Feature", backref="class_", lazy=True)
    subclasses = db.relationship("Subclass", backref="class_", lazy=True)

    def __repr__(self):
        return f"<Class {self.name}>"


class Subclass(db.Model):
    __tablename__ = "subclasses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"))
    features = db.Column(db.JSON)  # Class-specific features and abilities

    def __repr__(self):
        return f"<Subclass {self.name}>"


class Background(db.Model):
    __tablename__ = "backgrounds"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True, index=True)
    feature = db.Column(db.String)  # Special background feature
    skill_proficiencies = db.Column(db.JSON)  # e.g., ['Athletics', 'Perception']
    tool_proficiencies = db.Column(db.JSON)
    languages = db.Column(db.JSON)
    personality_traits = db.Column(db.JSON)
    ideals = db.Column(db.JSON)
    bonds = db.Column(db.JSON)
    flaws = db.Column(db.JSON)
    features = db.relationship("Feature", backref="background", lazy=True)

    def __repr__(self):
        return f"<Background {self.name}>"


class Feat(db.Model):
    __tablename__ = "feats"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.Text)
    prerequisites = db.Column(db.JSON)  # { 'level': 4, 'strength': 15 }

    def __repr__(self):
        return f"<Feat {self.name}>"


class Spell(db.Model):
    __tablename__ = "spells"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    level = db.Column(db.Integer)
    spell_type = db.Column(db.String)  # Evocation, Conjuration, etc.
    casting_time = db.Column(db.String)
    range = db.Column(db.String)
    components = db.Column(db.JSON)  # Verbal, Somatic, Material
    duration = db.Column(db.String)
    description = db.Column(db.Text)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"))

    def __repr__(self):
        return f"<Spell {self.name} (Level {self.level})>"


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    item_type = db.Column(
        db.String
    )  # Weapon, Armor, Shield, Adventuring Gear, Consumable
    weight = db.Column(db.Float)
    cost = db.Column(db.Integer)  # Gold pieces
    properties = db.Column(
        db.JSON
    )  # e.g., { 'damage': '1d8 slashing', 'range': '60/120' }
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<Item {self.name}>"


class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    ability = db.Column(db.String, nullable=False)  # e.g., 'Strength', 'Dexterity'

    def __repr__(self):
        return f"<Skill {self.name}>"


class SkillProficiency(db.Model):
    __tablename__ = "skill_proficiencies"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"))
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))
    proficient = db.Column(db.Boolean, default=False)

    skill = db.relationship("Skill")

    def __repr__(self):
        return f"<SkillProficiency {self.skill.name} on Character {self.character_id}>"


class Tool(db.Model):
    __tablename__ = "tools"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    tool_type = db.Column(db.String)  # e.g., 'Artisan's Tools', 'Gaming Set'

    def __repr__(self):
        return f"<Tool {self.name}>"


class ToolProficiency(db.Model):
    __tablename__ = "tool_proficiencies"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"))
    tool_id = db.Column(db.Integer, db.ForeignKey("tools.id"))

    tool = db.relationship("Tool")

    def __repr__(self):
        return f"<ToolProficiency {self.tool.name} on Character {self.character_id}>"


class Language(db.Model):
    __tablename__ = "languages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    def __repr__(self):
        return f"<Language {self.name}>"


class Proficiency(db.Model):
    __tablename__ = "proficiencies"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"))
    name = db.Column(db.String, nullable=False)  # Could be skill or tool
    type = db.Column(db.String, nullable=False)  # 'Skill' or 'Tool'

    def __repr__(self):
        return (
            f"<Proficiency {self.name} ({self.type}) on Character {self.character_id}>"
        )


class Feature(db.Model):
    __tablename__ = "features"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.Text)
    feature_type = db.Column(
        db.String, nullable=False
    )  # e.g., 'Race', 'Class', 'Background', 'Subclass'
    race_id = db.Column(db.Integer, db.ForeignKey("races.id"), nullable=True)
    subrace_id = db.Column(db.Integer, db.ForeignKey("subraces.id"), nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=True)
    background_id = db.Column(
        db.Integer, db.ForeignKey("backgrounds.id"), nullable=True
    )
    subclass_id = db.Column(db.Integer, db.ForeignKey("subclasses.id"), nullable=True)

    def __repr__(self):
        return f"<Feature {self.name} ({self.feature_type})>"


class Condition(db.Model):
    __tablename__ = "conditions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<Condition {self.name}>"


class CharacterCondition(db.Model):
    __tablename__ = "character_conditions"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"))
    condition_id = db.Column(db.Integer, db.ForeignKey("conditions.id"))
    duration = db.Column(db.Integer)  # In turns or minutes

    condition = db.relationship("Condition")

    def __repr__(self):
        return f"<CharacterCondition {self.condition.name} on Character {self.character_id}>"


def populate_defaults():
    # Skills
    skills = [
        {"name": "Athletics", "ability": "Strength"},
        {"name": "Acrobatics", "ability": "Dexterity"},
        {"name": "Sleight of Hand", "ability": "Dexterity"},
        {"name": "Stealth", "ability": "Dexterity"},
        {"name": "Arcana", "ability": "Intelligence"},
        {"name": "History", "ability": "Intelligence"},
        {"name": "Investigation", "ability": "Intelligence"},
        {"name": "Nature", "ability": "Intelligence"},
        {"name": "Religion", "ability": "Intelligence"},
        {"name": "Animal Handling", "ability": "Wisdom"},
        {"name": "Insight", "ability": "Wisdom"},
        {"name": "Medicine", "ability": "Wisdom"},
        {"name": "Perception", "ability": "Wisdom"},
        {"name": "Survival", "ability": "Wisdom"},
        {"name": "Deception", "ability": "Charisma"},
        {"name": "Intimidation", "ability": "Charisma"},
        {"name": "Performance", "ability": "Charisma"},
        {"name": "Persuasion", "ability": "Charisma"},
    ]
    for skill in skills:
        existing_skill = Skill.query.filter_by(name=skill["name"]).first()
        if not existing_skill:
            new_skill = Skill(name=skill["name"], ability=skill["ability"])
            db.session.add(new_skill)

    # Tools
    tools = [
        {"name": "Alchemist's Supplies", "tool_type": "Artisan's Tools"},
        {"name": "Brewer's Supplies", "tool_type": "Artisan's Tools"},
        {"name": "Calligrapher's Supplies", "tool_type": "Artisan's Tools"},
        {"name": "Carpenter's Tools", "tool_type": "Artisan's Tools"},
        {"name": "Cook's Utensils", "tool_type": "Artisan's Tools"},
        {"name": "Herbalism Kit", "tool_type": "Artisan's Tools"},
        {"name": "Smith's Tools", "tool_type": "Artisan's Tools"},
        {"name": "Thieves' Tools", "tool_type": "Thievery"},
        {"name": "Gaming Set", "tool_type": "Entertainment"},
        {"name": "Musical Instrument", "tool_type": "Entertainment"},
    ]
    for tool in tools:
        existing_tool = Tool.query.filter_by(name=tool["name"]).first()
        if not existing_tool:
            new_tool = Tool(name=tool["name"], tool_type=tool["tool_type"])
            db.session.add(new_tool)

    # Languages
    languages = [
        "Common",
        "Elvish",
        "Dwarvish",
        "Orcish",
        "Draconic",
        "Giant",
        "Gnomish",
        "Goblin",
        "Halfling",
        "Infernal",
        "Sylvan",
        "Undercommon",
        "Abyssal",
        "Celestial",
        "Primordial",
        "Auran",
        "Ignan",
        "Aquan",
        "Terran",
    ]
    for lang in languages:
        existing_lang = Language.query.filter_by(name=lang).first()
        if not existing_lang:
            new_lang = Language(name=lang)
            db.session.add(new_lang)

    # Races (Legal D&D 5e races)
    races = [
        {
            "name": "Human",
            "speed": 30,
            "ability_increases": {"all": 1},
            "size": "Medium",
            "darkvision": False,
        },
        {
            "name": "Elf",
            "speed": 30,
            "ability_increases": {"dexterity": 2},
            "size": "Medium",
            "darkvision": True,
        },
        {
            "name": "Dwarf",
            "speed": 25,
            "ability_increases": {"constitution": 2},
            "size": "Medium",
            "darkvision": True,
        },
        {
            "name": "Halfling",
            "speed": 25,
            "ability_increases": {"dexterity": 2},
            "size": "Small",
            "darkvision": False,
        },
        {
            "name": "Dragonborn",
            "speed": 30,
            "ability_increases": {"strength": 2, "charisma": 1},
            "size": "Medium",
            "darkvision": False,
        },
        {
            "name": "Gnome",
            "speed": 25,
            "ability_increases": {"intelligence": 2},
            "size": "Small",
            "darkvision": True,
        },
        {
            "name": "Half-Orc",
            "speed": 30,
            "ability_increases": {"strength": 2, "constitution": 1},
            "size": "Medium",
            "darkvision": True,
        },
        {
            "name": "Tiefling",
            "speed": 30,
            "ability_increases": {"intelligence": 1, "charisma": 2},
            "size": "Medium",
            "darkvision": True,
        },
        {
            "name": "Half-Elf",
            "speed": 30,
            "ability_increases": {"charisma": 2},
            "size": "Medium",
            "darkvision": True,
        },
        {
            "name": "Aasimar",
            "speed": 30,
            "ability_increases": {"charisma": 2},
            "size": "Medium",
            "darkvision": True,
        },
        {
            "name": "Tabaxi",
            "speed": 30,
            "ability_increases": {"dexterity": 2, "charisma": 1},
            "size": "Medium",
            "darkvision": True,
        },
        {
            "name": "Genasi",
            "speed": 30,
            "ability_increases": {"constitution": 2},
            "size": "Medium",
            "darkvision": False,
        },
        {
            "name": "Tortle",
            "speed": 30,
            "ability_increases": {"strength": 2, "wisdom": 1},
            "size": "Medium",
            "darkvision": False,
        },
        {
            "name": "Yuan-ti Pureblood",
            "speed": 30,
            "ability_increases": {"charisma": 2, "intelligence": 1},
            "size": "Medium",
            "darkvision": True,
        },
        # Add additional races from official sources (Eberron, Ravnica, etc.)
    ]
    for race in races:
        existing_race = Race.query.filter_by(name=race["name"]).first()
        if not existing_race:
            new_race = Race(
                name=race["name"],
                speed=race["speed"],
                ability_increases=race["ability_increases"],
                size=race["size"],
                darkvision=race["darkvision"],
            )
            db.session.add(new_race)

    # Classes (Legal D&D 5e classes)
    classes = [
        {"name": "Barbarian", "hit_die": 12, "primary_ability": "Strength"},
        {"name": "Bard", "hit_die": 8, "primary_ability": "Charisma"},
        {"name": "Cleric", "hit_die": 8, "primary_ability": "Wisdom"},
        {"name": "Druid", "hit_die": 8, "primary_ability": "Wisdom"},
        {"name": "Fighter", "hit_die": 10, "primary_ability": "Strength"},
        {"name": "Monk", "hit_die": 8, "primary_ability": "Dexterity"},
        {"name": "Paladin", "hit_die": 10, "primary_ability": "Charisma"},
        {"name": "Ranger", "hit_die": 10, "primary_ability": "Dexterity"},
        {"name": "Rogue", "hit_die": 8, "primary_ability": "Dexterity"},
        {"name": "Sorcerer", "hit_die": 6, "primary_ability": "Charisma"},
        {"name": "Warlock", "hit_die": 8, "primary_ability": "Charisma"},
        {"name": "Wizard", "hit_die": 6, "primary_ability": "Intelligence"},
        # Add more classes if necessary
    ]
    for char_class in classes:
        existing_class = Class.query.filter_by(name=char_class["name"]).first()
        if not existing_class:
            new_class = Class(
                name=char_class["name"],
                hit_die=char_class["hit_die"],
                primary_ability=char_class["primary_ability"],
            )
            db.session.add(new_class)

    # Backgrounds (Legal D&D 5e backgrounds)
    backgrounds = [
        {
            "name": "Acolyte",
            "feature": "Shelter of the Faithful",
            "skill_proficiencies": ["Insight", "Religion"],
        },
        {
            "name": "Charlatan",
            "feature": "False Identity",
            "skill_proficiencies": ["Deception", "Sleight of Hand"],
        },
        {
            "name": "Criminal",
            "feature": "Criminal Contact",
            "skill_proficiencies": ["Deception", "Stealth"],
        },
        {
            "name": "Entertainer",
            "feature": "By Popular Demand",
            "skill_proficiencies": ["Acrobatics", "Performance"],
        },
        {
            "name": "Folk Hero",
            "feature": "Rustic Hospitality",
            "skill_proficiencies": ["Animal Handling", "Survival"],
        },
        {
            "name": "Guild Artisan",
            "feature": "Guild Membership",
            "skill_proficiencies": ["Insight", "Persuasion"],
        },
        {
            "name": "Hermit",
            "feature": "Discovery",
            "skill_proficiencies": ["Medicine", "Religion"],
        },
        {
            "name": "Noble",
            "feature": "Position of Privilege",
            "skill_proficiencies": ["History", "Persuasion"],
        },
        {
            "name": "Outlander",
            "feature": "Wanderer",
            "skill_proficiencies": ["Athletics", "Survival"],
        },
        {
            "name": "Sage",
            "feature": "Researcher",
            "skill_proficiencies": ["Arcana", "History"],
        },
        {
            "name": "Sailor",
            "feature": "Ship's Passage",
            "skill_proficiencies": ["Athletics", "Perception"],
        },
        {
            "name": "Soldier",
            "feature": "Military Rank",
            "skill_proficiencies": ["Athletics", "Intimidation"],
        },
        {
            "name": "Urchin",
            "feature": "City Secrets",
            "skill_proficiencies": ["Sleight of Hand", "Stealth"],
        },
        # Add more backgrounds as needed
    ]
    for background in backgrounds:
        existing_background = Background.query.filter_by(
            name=background["name"]
        ).first()
        if not existing_background:
            new_background = Background(
                name=background["name"],
                feature=background["feature"],
                skill_proficiencies=background["skill_proficiencies"],
            )
            db.session.add(new_background)

    # Commit all data to the database
    db.session.commit()
