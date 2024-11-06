# models/character_models.py

from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, JSON, Text,
    Enum as SQLEnum, ForeignKey, Table
)
from sqlalchemy.orm import relationship, validates, Session

from db.database import Base  # Import Base from your database module

# Association tables
character_inventory = Table(
    "character_inventory", Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("item_id", Integer, ForeignKey("items.id"), primary_key=True),
)

character_feats = Table(
    "character_feats", Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("feat_id", Integer, ForeignKey("feats.id"), primary_key=True),
)

character_features = Table(
    "character_features", Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("feature_id", Integer, ForeignKey("features.id"), primary_key=True),
)

character_languages = Table(
    "character_languages", Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("language_id", Integer, ForeignKey("languages.id"), primary_key=True),
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

class Character(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=True)
    background_id = Column(Integer, ForeignKey("backgrounds.id"), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    alignment = Column(SQLEnum(AlignmentEnum), nullable=True)

    # Core Stats
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)

    # Ability Scores
    strength = Column(Integer, nullable=False)
    dexterity = Column(Integer, nullable=False)
    constitution = Column(Integer, nullable=False)
    intelligence = Column(Integer, nullable=False)
    wisdom = Column(Integer, nullable=False)
    charisma = Column(Integer, nullable=False)

    proficiency_bonus = Column(Integer, default=2)  # Increases with level

    # Combat-related attributes
    max_hit_points = Column(Integer, nullable=False, default=10)
    current_hit_points = Column(Integer, nullable=False, default=10)
    temporary_hit_points = Column(Integer, default=0)
    armor_class = Column(Integer, nullable=False, default=10)
    initiative = Column(Integer, default=0)  # Typically Dex modifier
    speed = Column(Integer, nullable=False, default=30)  # Base walking speed

    # Death saves
    death_saves_successes = Column(Integer, default=0)
    death_saves_failures = Column(Integer, default=0)

    # Relationships
    race = relationship("Race", backref="characters")
    background = relationship("Background", backref="characters")
    character_class = relationship("Class", backref="characters")
    inventory = relationship(
        "Item",
        secondary=character_inventory,
        backref="owners",
    )
    feats = relationship(
        "Feat",
        secondary=character_feats,
        backref="characters",
    )
    features = relationship(
        "Feature",
        secondary=character_features,
        backref="characters",
    )
    spells = relationship("Spell", backref="character")
    languages = relationship(
        "Language",
        secondary=character_languages,
        backref="characters",
    )
    conditions = relationship("CharacterCondition", backref="character")
    proficiencies = relationship("Proficiency", backref="character")

    # Saving Throws
    strength_save = Column(Boolean, default=False)
    dexterity_save = Column(Boolean, default=False)
    constitution_save = Column(Boolean, default=False)
    intelligence_save = Column(Boolean, default=False)
    wisdom_save = Column(Boolean, default=False)
    charisma_save = Column(Boolean, default=False)

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
        return self.dexterity_mod + (self.proficiency_bonus if self.dexterity_save else 0)

    @property
    def constitution_save_bonus(self):
        return self.constitution_mod + (self.proficiency_bonus if self.constitution_save else 0)

    @property
    def intelligence_save_bonus(self):
        return self.intelligence_mod + (self.proficiency_bonus if self.intelligence_save else 0)

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

class Race(Base):
    __tablename__ = "races"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    ability_increases = Column(JSON)  # e.g., { 'dexterity': 2, 'intelligence': 1 }
    size = Column(String)  # Medium, Small, etc.
    speed = Column(Integer)
    darkvision = Column(Boolean, default=False)
    traits = Column(JSON)  # Racial traits
    subraces = relationship("Subrace", backref="race")
    features = relationship("Feature", backref="race")

    def __repr__(self):
        return f"<Race {self.name}>"

class Subrace(Base):
    __tablename__ = "subraces"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    race_id = Column(Integer, ForeignKey("races.id"))
    ability_increases = Column(JSON)  # Subrace ability modifiers
    traits = Column(JSON)  # Subrace-specific traits
    features = relationship("Feature", backref="subrace")

    def __repr__(self):
        return f"<Subrace {self.name}>"

class Class(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    hit_die = Column(Integer)  # e.g., 6, 8, etc.
    primary_ability = Column(String)  # e.g., 'Charisma', 'Intelligence', etc.
    saving_throw_proficiencies = Column(JSON)  # e.g., { 'strength': True, 'dexterity': False }
    proficiencies = Column(JSON)  # Weapons, armor, tools
    subclass_available = Column(Boolean, default=True)
    features = relationship("Feature", backref="class_")
    subclasses = relationship("Subclass", backref="class_")

    def __repr__(self):
        return f"<Class {self.name}>"

class Subclass(Base):
    __tablename__ = "subclasses"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"))
    features = Column(JSON)  # Class-specific features and abilities

    def __repr__(self):
        return f"<Subclass {self.name}>"

class Background(Base):
    __tablename__ = "backgrounds"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    feature = Column(String)  # Special background feature
    skill_proficiencies = Column(JSON)  # e.g., ['Athletics', 'Perception']
    tool_proficiencies = Column(JSON)
    languages = Column(JSON)
    personality_traits = Column(JSON)
    ideals = Column(JSON)
    bonds = Column(JSON)
    flaws = Column(JSON)
    features = relationship("Feature", backref="background")

    def __repr__(self):
        return f"<Background {self.name}>"

class Feat(Base):
    __tablename__ = "feats"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    prerequisites = Column(JSON)  # e.g., { 'level': 4, 'strength': 15 }

    def __repr__(self):
        return f"<Feat {self.name}>"

class Spell(Base):
    __tablename__ = "spells"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    level = Column(Integer)
    spell_type = Column(String)  # e.g., 'Evocation', 'Conjuration', etc.
    casting_time = Column(String)
    range = Column(String)
    components = Column(JSON)  # Verbal, Somatic, Material
    duration = Column(String)
    description = Column(Text)
    character_id = Column(Integer, ForeignKey("characters.id"))

    def __repr__(self):
        return f"<Spell {self.name} (Level {self.level})>"

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    item_type = Column(String)  # Weapon, Armor, Shield, Adventuring Gear, Consumable
    weight = Column(Float)
    cost = Column(Integer)  # Gold pieces
    properties = Column(JSON)  # e.g., { 'damage': '1d8 slashing', 'range': '60/120' }
    description = Column(Text)

    def __repr__(self):
        return f"<Item {self.name}>"

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    ability = Column(String, nullable=False)  # e.g., 'Strength', 'Dexterity'

    def __repr__(self):
        return f"<Skill {self.name}>"

class SkillProficiency(Base):
    __tablename__ = "skill_proficiencies"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    proficient = Column(Boolean, default=False)

    skill = relationship("Skill")

    def __repr__(self):
        return f"<SkillProficiency {self.skill.name} on Character {self.character_id}>"

class Tool(Base):
    __tablename__ = "tools"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    tool_type = Column(String)  # e.g., 'Artisan's Tools', 'Gaming Set'

    def __repr__(self):
        return f"<Tool {self.name}>"

class ToolProficiency(Base):
    __tablename__ = "tool_proficiencies"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    tool_id = Column(Integer, ForeignKey("tools.id"))

    tool = relationship("Tool")

    def __repr__(self):
        return f"<ToolProficiency {self.tool.name} on Character {self.character_id}>"

class Language(Base):
    __tablename__ = "languages"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return f"<Language {self.name}>"

class Proficiency(Base):
    __tablename__ = "proficiencies"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    name = Column(String, nullable=False)  # Could be skill or tool
    type = Column(String, nullable=False)  # 'Skill' or 'Tool'

    def __repr__(self):
        return f"<Proficiency {self.name} ({self.type}) on Character {self.character_id}>"

class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    feature_type = Column(String, nullable=False)  # e.g., 'Race', 'Class', 'Background', 'Subclass'
    race_id = Column(Integer, ForeignKey("races.id"), nullable=True)
    subrace_id = Column(Integer, ForeignKey("subraces.id"), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    background_id = Column(Integer, ForeignKey("backgrounds.id"), nullable=True)
    subclass_id = Column(Integer, ForeignKey("subclasses.id"), nullable=True)

    def __repr__(self):
        return f"<Feature {self.name} ({self.feature_type})>"

class Condition(Base):
    __tablename__ = "conditions"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    def __repr__(self):
        return f"<Condition {self.name}>"

class CharacterCondition(Base):
    __tablename__ = "character_conditions"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    condition_id = Column(Integer, ForeignKey("conditions.id"))
    duration = Column(Integer)  # In turns or minutes

    condition = relationship("Condition")

    def __repr__(self):
        return f"<CharacterCondition {self.condition.name} on Character {self.character_id}>"

def populate_defaults(session: Session):
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
        if not session.query(Skill).filter_by(name=skill["name"]).first():
            new_skill = Skill(name=skill["name"], ability=skill["ability"])
            session.add(new_skill)

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
        if not session.query(Tool).filter_by(name=tool["name"]).first():
            new_tool = Tool(name=tool["name"], tool_type=tool["tool_type"])
            session.add(new_tool)

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
        if not session.query(Language).filter_by(name=lang).first():
            new_lang = Language(name=lang)
            session.add(new_lang)

    # Races
    races = [
        {
            "name": "Human",
            "speed": 30,
            "ability_increases": {"all": 1},
            "size": "Medium",
            "darkvision": False,
        },
        {
            "name": "Dwarf",
            "speed": 25,
            "ability_increases": {"constitution": 2},
            "size": "Medium",
            "darkvision": True,
            "traits": {"dwarven_resilience": "You have advantage on saving throws against poison."}
        },
        {
            "name": "Elf",
            "speed": 30,
            "ability_increases": {"dexterity": 2},
            "size": "Medium",
            "darkvision": True,
            "traits": {"fey_ancestry": "You have advantage on saving throws against being charmed."}
        },
        {
            "name": "Halfling",
            "speed": 25,
            "ability_increases": {"dexterity": 2},
            "size": "Small",
            "darkvision": False,
            "traits": {"lucky": "You can reroll a 1 on any d20 roll."}
        },
        {
            "name": "Dragonborn",
            "speed": 30,
            "ability_increases": {"strength": 2, "charisma": 1},
            "size": "Medium",
            "darkvision": False,
            "traits": {"breath_weapon": "You can use a breath weapon attack based on your draconic ancestry."}
        },
        {
            "name": "Gnome",
            "speed": 25,
            "ability_increases": {"intelligence": 2},
            "size": "Small",
            "darkvision": True,
            "traits": {
                "gnome_cunning": "You have advantage on all Intelligence, Wisdom, and Charisma saving throws against magic."}
        },
        {
            "name": "Half-Elf",
            "speed": 30,
            "ability_increases": {"charisma": 2, "choice1": 1, "choice2": 1},
            "size": "Medium",
            "darkvision": True,
            "traits": {"fey_ancestry": "You have advantage on saving throws against being charmed."}
        },
        {
            "name": "Half-Orc",
            "speed": 30,
            "ability_increases": {"strength": 2, "constitution": 1},
            "size": "Medium",
            "darkvision": True,
            "traits": {"relentless_endurance": "When reduced to 0 HP but not killed, you can drop to 1 HP instead."}
        },
        {
            "name": "Tiefling",
            "speed": 30,
            "ability_increases": {"charisma": 2, "intelligence": 1},
            "size": "Medium",
            "darkvision": True,
            "traits": {"hellish_resistance": "You have resistance to fire damage."}
        },
        {
            "name": "Aasimar",
            "speed": 30,
            "ability_increases": {"charisma": 2},
            "size": "Medium",
            "darkvision": True,
            "traits": {"healing_hands": "You can heal others with a touch."}
        },
        {
            "name": "Tabaxi",
            "speed": 30,
            "ability_increases": {"dexterity": 2, "charisma": 1},
            "size": "Medium",
            "darkvision": True,
            "traits": {"feline_agility": "You can double your speed until the end of the turn."}
        },
        {
            "name": "Genasi",
            "speed": 30,
            "ability_increases": {"constitution": 2},
            "size": "Medium",
            "darkvision": False,
            "traits": {
                "elemental_affinity": "You have abilities based on your elemental ancestry (Air, Earth, Fire, Water)."}
        },
        {
            "name": "Tortle",
            "speed": 30,
            "ability_increases": {"strength": 2, "wisdom": 1},
            "size": "Medium",
            "darkvision": False,
            "traits": {"natural_armor": "You have a base AC of 17 while unarmored."}
        },
        {
            "name": "Yuan-ti Pureblood",
            "speed": 30,
            "ability_increases": {"charisma": 2, "intelligence": 1},
            "size": "Medium",
            "darkvision": True,
            "traits": {"magic_resistance": "You have advantage on saving throws against spells and magical effects."}
        },
        {
            "name": "Firbolg",
            "speed": 30,
            "ability_increases": {"wisdom": 2, "strength": 1},
            "size": "Medium",
            "darkvision": False,
            "traits": {"firbolg_magic": "You can cast Detect Magic and Disguise Self once per short rest."}
        },
        {
            "name": "Goliath",
            "speed": 30,
            "ability_increases": {"strength": 2, "constitution": 1},
            "size": "Medium",
            "darkvision": False,
            "traits": {"powerful_build": "You count as one size larger when determining carrying capacity."}
        },
        {
            "name": "Kenku",
            "speed": 30,
            "ability_increases": {"dexterity": 2, "wisdom": 1},
            "size": "Medium",
            "darkvision": False,
            "traits": {"mimicry": "You can mimic sounds you have heard."}
        },
        {
            "name": "Lizardfolk",
            "speed": 30,
            "ability_increases": {"constitution": 2, "wisdom": 1},
            "size": "Medium",
            "darkvision": False,
            "traits": {"natural_armor": "Your AC is 13 + Dexterity modifier while unarmored."}
        },
        {
            "name": "Triton",
            "speed": 30,
            "ability_increases": {"strength": 1, "constitution": 1, "charisma": 1},
            "size": "Medium",
            "darkvision": True,
            "traits": {"amphibious": "You can breathe air and water."}
        }
        # You can add more races and subraces as desired
    ]

    for race in races:
        if not session.query(Race).filter_by(name=race["name"]).first():
            new_race = Race(
                name=race["name"],
                speed=race["speed"],
                ability_increases=race["ability_increases"],
                size=race["size"],
                darkvision=race["darkvision"],
                traits=race.get("traits", {}),
            )
            session.add(new_race)

    # Classes
    classes = [
        {
            "name": "Barbarian",
            "hit_die": 12,
            "primary_ability": "Strength",
            "saving_throw_proficiencies": {"strength": True, "constitution": True},
            "proficiencies": {"weapons": ["simple", "martial"], "armor": ["light", "medium", "shields"]},
            
        },
        {
            "name": "Bard",
            "hit_die": 8,
            "primary_ability": "Charisma",
            "saving_throw_proficiencies": {"dexterity": True, "charisma": True},
            "proficiencies": {"weapons": ["simple"], "armor": ["light"]},
            
        },
        {
            "name": "Cleric",
            "hit_die": 8,
            "primary_ability": "Wisdom",
            "saving_throw_proficiencies": {"wisdom": True, "charisma": True},
            "proficiencies": {"weapons": ["simple"], "armor": ["light", "medium", "shields"]},
            
        },
        {
            "name": "Druid",
            "hit_die": 8,
            "primary_ability": "Wisdom",
            "saving_throw_proficiencies": {"intelligence": True, "wisdom": True},
            "proficiencies": {
                "weapons": ["clubs", "daggers", "darts", "javelins", "maces", "quarterstaffs", "scimitars", "sickles",
                            "slings", "spears"], "armor": ["light", "medium (no metal)", "shields (no metal)"]},
            
        },
        {
            "name": "Fighter",
            "hit_die": 10,
            "primary_ability": "Strength or Dexterity",
            "saving_throw_proficiencies": {"strength": True, "constitution": True},
            "proficiencies": {"weapons": ["simple", "martial"], "armor": ["light", "medium", "heavy", "shields"]},
            
        },
        {
            "name": "Monk",
            "hit_die": 8,
            "primary_ability": "Dexterity and Wisdom",
            "saving_throw_proficiencies": {"strength": True, "dexterity": True},
            "proficiencies": {"weapons": ["simple", "shortswords"], "armor": []},
            
        },
        {
            "name": "Paladin",
            "hit_die": 10,
            "primary_ability": "Charisma and Strength",
            "saving_throw_proficiencies": {"wisdom": True, "charisma": True},
            "proficiencies": {"weapons": ["simple", "martial"], "armor": ["light", "medium", "heavy", "shields"]},
            
        },
        {
            "name": "Ranger",
            "hit_die": 10,
            "primary_ability": "Dexterity and Wisdom",
            "saving_throw_proficiencies": {"strength": True, "dexterity": True},
            "proficiencies": {"weapons": ["simple", "martial"], "armor": ["light", "medium", "shields"]},
            
        },
        {
            "name": "Rogue",
            "hit_die": 8,
            "primary_ability": "Dexterity",
            "saving_throw_proficiencies": {"dexterity": True, "intelligence": True},
            "proficiencies": {"weapons": ["simple", "hand_crossbows", "longswords", "rapiers", "shortswords"],
                              "armor": ["light"]},
            
        },
        {
            "name": "Sorcerer",
            "hit_die": 6,
            "primary_ability": "Charisma",
            "saving_throw_proficiencies": {"constitution": True, "charisma": True},
            "proficiencies": {"weapons": ["daggers", "darts", "slings", "quarterstaffs", "light_crossbows"],
                              "armor": []},
            
        },
        {
            "name": "Warlock",
            "hit_die": 8,
            "primary_ability": "Charisma",
            "saving_throw_proficiencies": {"wisdom": True, "charisma": True},
            "proficiencies": {"weapons": ["simple"], "armor": ["light"]},
            
        },
        {
            "name": "Wizard",
            "hit_die": 6,
            "primary_ability": "Intelligence",
            "saving_throw_proficiencies": {"intelligence": True, "wisdom": True},
            "proficiencies": {"weapons": ["daggers", "darts", "slings", "quarterstaffs", "light_crossbows"],
                              "armor": []},
            
        },
        {
            "name": "Artificer",
            "hit_die": 8,
            "primary_ability": "Intelligence",
            "saving_throw_proficiencies": {"constitution": True, "intelligence": True},
            "proficiencies": {"weapons": ["simple"], "armor": ["light", "medium", "shields"]},
            
        }
    ]

    for char_class in classes:
        if not session.query(Class).filter_by(name=char_class["name"]).first():
            new_class = Class(
                name=char_class["name"],
                hit_die=char_class["hit_die"],
                primary_ability=char_class["primary_ability"],
                saving_throw_proficiencies=char_class["saving_throw_proficiencies"],
                proficiencies=char_class["proficiencies"],
            )
            session.add(new_class)

    # Backgrounds
    backgrounds = [
        {
            "name": "Acolyte",
            "feature": "Shelter of the Faithful",
            "skill_proficiencies": ["Insight", "Religion"],
            "tool_proficiencies": [],
            "languages": ["Two of your choice"],
            "personality_traits": [
                "I respect all faiths and seek to understand other religions.",
                "I am always calm, even in the face of chaos.",
                "I see omens in every event and action.",
                "I have spent so long in the temple that I have little practical experience dealing with people in the outside world.",
            ],
            "ideals": [
                "Tradition: The ancient traditions of worship must be preserved.",
                "Charity: I always try to help those in need.",
                "Change: We must help bring about the changes the gods are constantly working in the world.",
                "Faith: I trust that my deity will guide my actions.",
                "Aspiration: I seek to prove myself worthy of my god's favor.",
            ],
            "bonds": [
                "I would die to recover an ancient artifact of my faith.",
                "I owe my life to the priest who took me in when I was an orphan.",
                "Everything I do is for the common people.",
                "I will do anything to protect the temple where I served.",
            ],
            "flaws": [
                "I judge others harshly and myself even more severely.",
                "I put too much trust in those who wield power within my temple.",
                "My piety sometimes leads me to blindly trust those that profess faith in my god.",
                "I am inflexible in my thinking.",
            ],
        },
        {
            "name": "Charlatan",
            "feature": "False Identity",
            "skill_proficiencies": ["Deception", "Sleight of Hand"],
            "tool_proficiencies": ["Disguise kit", "Forgery kit"],
            "languages": [],
            "personality_traits": [
                "I fall in and out of love easily and am always pursuing someone.",
                "I have a joke for every occasion.",
                "Flattery is my preferred trick for getting what I want.",
                "I'm a born gambler who can't resist taking a risk.",
            ],
            "ideals": [
                "Independence: I am a free spirit—no one tells me what to do.",
                "Fairness: I never target people who can't afford to lose a few coins.",
                "Charity: I distribute the money I acquire to the people who really need it.",
                "Creativity: I never run the same con twice.",
            ],
            "bonds": [
                "I fleeced the wrong person and must work to ensure that this individual never crosses paths with me or those I care about.",
                "I owe everything to my mentor—a horrible person who's probably rotting in jail somewhere.",
                "Somewhere out there, I have a child who doesn't know me.",
                "I come from a noble family, and one day I'll reclaim my lands and title from those who stole them from me.",
            ],
            "flaws": [
                "I can't resist a pretty face.",
                "I'm always in debt.",
                "I'm convinced that no one could ever fool me the way I fool others.",
                "I hate to admit it and will hate myself for it, but I'll run and preserve my own hide if the going gets tough.",
            ],
        },
        {
            "name": "Criminal",
            "feature": "Criminal Contact",
            "skill_proficiencies": ["Deception", "Stealth"],
            "tool_proficiencies": ["One type of gaming set", "Thieves' tools"],
            "languages": [],
            "personality_traits": [
                "I always have a plan for what to do when things go wrong.",
                "I am always calm, no matter the situation.",
                "The first thing I do in a new place is note the locations of everything valuable.",
                "I would rather make a new friend than a new enemy.",
            ],
            "ideals": [
                "Honor: I don't steal from others in the trade.",
                "Freedom: Chains are meant to be broken.",
                "Charity: I steal from the wealthy so that I can help people in need.",
                "Greed: I will do whatever it takes to become wealthy.",
            ],
            "bonds": [
                "I'm trying to pay off an old debt I owe to a generous benefactor.",
                "My ill-gotten gains go to support my family.",
                "Something important was taken from me, and I aim to steal it back.",
                "I will become the greatest thief that ever lived.",
            ],
            "flaws": [
                "When I see something valuable, I can't think about anything but how to steal it.",
                "I turn tail and run when things look bad.",
                "An innocent person is in prison for a crime that I committed.",
                "I can't resist taking risks to get a big payoff.",
            ],
        },
        {
            "name": "Entertainer",
            "feature": "By Popular Demand",
            "skill_proficiencies": ["Acrobatics", "Performance"],
            "tool_proficiencies": ["Disguise kit", "One type of musical instrument"],
            "languages": [],
            "personality_traits": [
                "I know a story relevant to almost every situation.",
                "Whenever I come to a new place, I collect local rumors.",
                "I'm a hopeless romantic, always searching for that 'special someone'.",
                "I love a good insult, even one directed at me.",
            ],
            "ideals": [
                "Beauty: When I perform, I make the world better than it was.",
                "Tradition: The stories, legends, and songs of the past must never be forgotten.",
                "Creativity: The world is in need of new ideas and bold action.",
                "Greed: I'm only in it for the money and fame.",
            ],
            "bonds": [
                "My instrument is my most treasured possession.",
                "Someone stole my precious instrument, and someday I'll get it back.",
                "I want to be famous, whatever it takes.",
                "I idolize a hero of the old tales and measure my deeds against theirs.",
            ],
            "flaws": [
                "I'll do anything to win fame and renown.",
                "I'm a sucker for a pretty face.",
                "A scandal prevents me from ever going home again.",
                "I once satirized a noble who still wants my head.",
            ],
        },
        {
            "name": "Folk Hero",
            "feature": "Rustic Hospitality",
            "skill_proficiencies": ["Animal Handling", "Survival"],
            "tool_proficiencies": ["One type of artisan's tools", "Vehicles (land)"],
            "languages": [],
            "personality_traits": [
                "I judge people by their actions, not their words.",
                "If someone is in trouble, I'm always ready to lend help.",
                "When I set my mind to something, I follow through.",
                "I have a strong sense of fair play and always try to find the most equitable solution.",
            ],
            "ideals": [
                "Respect: People deserve to be treated with dignity.",
                "Fairness: No one should get preferential treatment before the law.",
                "Freedom: Tyrants must not be allowed to oppress the people.",
                "Sincerity: There's no good in pretending to be something I'm not.",
            ],
            "bonds": [
                "I have a family that I love, and I'll do anything to protect them.",
                "I worked the land, I love the land, and I will protect the land.",
                "A proud noble once gave me a horrible beating, and I will take my revenge.",
                "My tools are symbols of my past life, and I carry them so that I will never forget my roots.",
            ],
            "flaws": [
                "The tyrant who rules my land will stop at nothing to see me killed.",
                "I'm convinced of the significance of my destiny, and blind to my shortcomings.",
                "I'm stubborn and don't take advice well.",
                "I have trouble trusting in my allies.",
            ],
        },
        {
            "name": "Guild Artisan",
            "feature": "Guild Membership",
            "skill_proficiencies": ["Insight", "Persuasion"],
            "tool_proficiencies": ["One type of artisan's tools"],
            "languages": ["One of your choice"],
            "personality_traits": [
                "I believe that anything worth doing is worth doing right.",
                "I'm rude to people who lack my commitment to hard work.",
                "I like to talk at length about my profession.",
                "I am utterly loyal to my guild.",
            ],
            "ideals": [
                "Community: It is the duty of all to strengthen the bonds of community.",
                "Generosity: My talents were given to me so that I could use them to benefit the world.",
                "Freedom: Everyone should be free to pursue their own livelihood.",
                "Aspiration: I work hard to be the best there is at my craft.",
            ],
            "bonds": [
                "The workshop where I learned my trade is the most important place in the world to me.",
                "I created a great work for someone, and found them unworthy to receive it.",
                "I owe my guild a great debt for forging me into the person I am today.",
                "I pursue wealth to secure someone's love.",
            ],
            "flaws": [
                "I'll do anything to get my hands on something rare or priceless.",
                "I'm quick to assume that someone is trying to cheat me.",
                "No one must ever learn that I once stole money from guild coffers.",
                "I'm never satisfied with what I have—I always want more.",
            ],
        },
        {
            "name": "Hermit",
            "feature": "Discovery",
            "skill_proficiencies": ["Medicine", "Religion"],
            "tool_proficiencies": ["Herbalism kit"],
            "languages": ["One of your choice"],
            "personality_traits": [
                "I've been isolated for so long that I rarely speak.",
                "I am utterly serene, even in the face of disaster.",
                "The leader of my community had something wise to say on every topic.",
                "I connect everything that happens to me to a grand cosmic plan.",
            ],
            "ideals": [
                "Greater Good: My gifts are meant to be shared with all.",
                "Logic: Emotions must not cloud our sense of what is right.",
                "Free Thinking: Inquiry and curiosity are the pillars of progress.",
                "Live and Let Live: Meddling in the affairs of others only causes trouble.",
            ],
            "bonds": [
                "I am still seeking the enlightenment I pursued in my seclusion.",
                "I entered seclusion to hide from those who might still be hunting me.",
                "I am devoted to a spiritual leader or teacher.",
                "I must protect a sacred text that carries answers to important questions.",
            ],
            "flaws": [
                "Now that I've returned to the world, I enjoy its delights a little too much.",
                "I harbor dark thoughts that my isolation failed to quell.",
                "I am dogmatic in my thoughts and philosophy.",
                "I let my need to win arguments overshadow friendships and harmony.",
            ],
        },
        {
            "name": "Noble",
            "feature": "Position of Privilege",
            "skill_proficiencies": ["History", "Persuasion"],
            "tool_proficiencies": ["One type of gaming set"],
            "languages": ["One of your choice"],
            "personality_traits": [
                "My eloquent flattery makes everyone I talk to feel important.",
                "The common folk love me for my kindness.",
                "No one could doubt by looking at my regal bearing that I am a cut above the unwashed masses.",
                "I take great pains to always look my best.",
            ],
            "ideals": [
                "Respect: Respect is due to me because of my position.",
                "Responsibility: It is my duty to respect the authority of those above me.",
                "Independence: I must prove that I can handle myself without the coddling of my family.",
                "Power: If I can attain more power, no one will tell me what to do.",
            ],
            "bonds": [
                "I will face any challenge to win the approval of my family.",
                "My house's alliance with another noble family must be sustained.",
                "Nothing is more important than the other members of my family.",
                "I am in love with the heir of a family that my family despises.",
            ],
            "flaws": [
                "I secretly believe that everyone is beneath me.",
                "I hide a truly scandalous secret that could ruin my family forever.",
                "I too often hear veiled insults and threats in every word addressed to me.",
                "I have an insatiable desire for carnal pleasures.",
            ],
        },
        {
            "name": "Outlander",
            "feature": "Wanderer",
            "skill_proficiencies": ["Athletics", "Survival"],
            "tool_proficiencies": ["One type of musical instrument"],
            "languages": ["One of your choice"],
            "personality_traits": [
                "I'm driven by a wanderlust that led me away from home.",
                "I watch over my friends as if they were a newborn litter.",
                "I once ran twenty-five miles without stopping.",
                "I have a lesson for every situation, drawn from observing nature.",
            ],
            "ideals": [
                "Change: Life is like the seasons, in constant change.",
                "Greater Good: It is each person's responsibility to make the most happiness for all.",
                "Honor: If I dishonor myself, I dishonor my whole clan.",
                "Might: The strongest are meant to rule.",
            ],
            "bonds": [
                "My family, clan, or tribe is the most important thing in my life.",
                "An injury to the unspoiled wilderness is an injury to me.",
                "I will bring terrible wrath down on the evildoers who destroyed my homeland.",
                "I am the last of my tribe, and it is up to me to ensure their names enter legend.",
            ],
            "flaws": [
                "I am too enamored of ale, wine, and other intoxicants.",
                "There's no room for caution in a life lived to the fullest.",
                "I remember every insult I've received and nurse a silent resentment.",
                "I am slow to trust members of other races.",
            ],
        },
        {
            "name": "Sage",
            "feature": "Researcher",
            "skill_proficiencies": ["Arcana", "History"],
            "tool_proficiencies": [],
            "languages": ["Two of your choice"],
            "personality_traits": [
                "I use polysyllabic words that convey the impression of great erudition.",
                "I've read every book in the world's greatest libraries.",
                "I'm used to helping out those who aren't as smart as I am.",
                "There's nothing I like more than a good mystery.",
            ],
            "ideals": [
                "Knowledge: The path to power is through knowledge.",
                "Beauty: What is beautiful points us beyond itself.",
                "Logic: Emotions must not cloud logical thinking.",
                "No Limits: Nothing should fetter the infinite possibility inherent in all existence.",
            ],
            "bonds": [
                "It is my duty to protect my students.",
                "I have an ancient text that holds terrible secrets.",
                "I've been searching my whole life for the answer to a certain question.",
                "I sold my soul for knowledge.",
            ],
            "flaws": [
                "I am easily distracted by the promise of information.",
                "Most people scream and run when they see a demon.",
                "Unlocking an ancient mystery is worth the price of a civilization.",
                "I speak without thinking through the consequences.",
            ],
        },
        {
            "name": "Sailor",
            "feature": "Ship's Passage",
            "skill_proficiencies": ["Athletics", "Perception"],
            "tool_proficiencies": ["Navigator's tools", "Vehicles (water)"],
            "languages": [],
            "personality_traits": [
                "My friends know they can rely on me.",
                "I work hard so that I can play hard when the work is done.",
                "I enjoy sailing into new ports and making new friends.",
                "I stretch the truth for the sake of a good story.",
            ],
            "ideals": [
                "Respect: The thing that keeps a ship together is mutual respect.",
                "Fairness: We all do the work, so we all share in the rewards.",
                "Freedom: The sea is freedom—the freedom to go anywhere and do anything.",
                "Mastery: I'm a predator, and the other ships on the sea are my prey.",
            ],
            "bonds": [
                "I'm loyal to my captain first, everything else second.",
                "The ship is most important—crewmates and captains come and go.",
                "I'll always remember my first ship.",
                "In a harbor town, I have a paramour whose eyes nearly stole me from the sea.",
            ],
            "flaws": [
                "I follow orders, even if I think they're wrong.",
                "I'll say anything to avoid having to do extra work.",
                "Once someone questions my courage, I never back down.",
                "I can't help but pocket loose coins and other trinkets I come across.",
            ],
        },
        {
            "name": "Soldier",
            "feature": "Military Rank",
            "skill_proficiencies": ["Athletics", "Intimidation"],
            "tool_proficiencies": ["One type of gaming set", "Vehicles (land)"],
            "languages": [],
            "personality_traits": [
                "I'm always polite and respectful.",
                "I'm haunted by memories of war.",
                "I've lost too many friends, and I'm slow to make new ones.",
                "I'm full of inspiring and cautionary tales from my military experience.",
            ],
            "ideals": [
                "Greater Good: Our lot is to lay down our lives in defense of others.",
                "Responsibility: I do what I must and obey just authority.",
                "Independence: When people follow orders blindly, they embrace a kind of tyranny.",
                "Glory: I must earn glory in battle.",
            ],
            "bonds": [
                "I would still lay down my life for the people I served with.",
                "Someone saved my life on the battlefield.",
                "My honor is my life.",
                "I'll never forget the crushing defeat my company suffered.",
            ],
            "flaws": [
                "The monstrous enemy we faced in battle still leaves me quivering.",
                "I have little respect for anyone who is not a proven warrior.",
                "I made a terrible mistake in battle that cost many lives.",
                "I enjoy the thrill of battle and sometimes cannot control myself.",
            ],
        },
        {
            "name": "Urchin",
            "feature": "City Secrets",
            "skill_proficiencies": ["Sleight of Hand", "Stealth"],
            "tool_proficiencies": ["Disguise kit", "Thieves' tools"],
            "languages": [],
            "personality_traits": [
                "I hide scraps of food and trinkets away in my pockets.",
                "I ask a lot of questions.",
                "I like to squeeze into small places where no one else can get to me.",
                "I sleep with my back to a wall or tree.",
            ],
            "ideals": [
                "Respect: All people, rich or poor, deserve respect.",
                "Community: We have to take care of each other.",
                "Change: The low are lifted up, and the high are brought down.",
                "Retribution: The rich need to be shown what life is like on the other side.",
            ],
            "bonds": [
                "My town or city is my home, and I'll fight to defend it.",
                "I sponsor an orphanage to keep others from enduring what I did.",
                "I owe my survival to another urchin who taught me to live on the streets.",
                "I owe a debt I can never repay to the person who took pity on me.",
            ],
            "flaws": [
                "If I'm outnumbered, I will run away from a fight.",
                "Gold seems like a lot of money to me, and I'll do just about anything for more of it.",
                "I will never fully trust anyone other than myself.",
                "It's not stealing if I need it more than someone else.",
            ],
        },
    ]

    for background in backgrounds:
        if not session.query(Background).filter_by(name=background["name"]).first():
            new_background = Background(
                name=background["name"],
                feature=background["feature"],
                skill_proficiencies=background["skill_proficiencies"],
                tool_proficiencies=background.get("tool_proficiencies", []),
                languages=background.get("languages", []),
                personality_traits=background.get("personality_traits", []),
                ideals=background.get("ideals", []),
                bonds=background.get("bonds", []),
                flaws=background.get("flaws", []),
            )
            session.add(new_background)

    # Commit all data to the database
    session.commit()
