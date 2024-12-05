# utils/utils.py

def get_skill_modifier(character, skill, proficiency_bonus=None):
    skill_to_ability = {
    "Athletics": "strength",
    "Acrobatics": "dexterity",
    "Sleight of Hand": "dexterity",
    "Stealth": "dexterity",
    "Arcana": "intelligence",
    "History": "intelligence",
    "Investigation": "intelligence",
    "Nature": "intelligence",
    "Religion": "intelligence",
    "Animal Handling": "wisdom",
    "Insight": "wisdom",
    "Medicine": "wisdom",
    "Perception": "wisdom",
    "Survival": "wisdom",
    "Deception": "charisma",
    "Intimidation": "charisma",
    "Performance": "charisma",
    "Persuasion": "charisma",
    }

    # Map skill to ability
    ability = skill_to_ability.get(skill)

    character_ability = character.get(f"{ability}")

    modifier = (character_ability - 10) // 2
    return modifier