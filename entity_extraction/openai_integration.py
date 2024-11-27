# entity_extraction/openai_integration.py

import openai
import json
from typing import List
import os
from dotenv import load_dotenv


load_dotenv()


openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_relations(text: str) -> str:
    """
    Uses OpenAI to extract relationships from text.
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant that extracts entities and their relationships from text."},
        {"role": "user", "content": f"""
        Extract all entities and their relationships from the following text and present them as a list of triples (subject, relation, object)
        "{text}"

        Triples:
        """}
    ]
    response = openai.chat.completions.create(
      model="gpt-4o",
      messages=messages,
      max_tokens=2000,
      temperature=0
  )
    return response.choices[0].message.content

def resolve_coreferences(text: str) -> str:
    """
    Uses OpenAI to resolve coreferences in text.
    """
    messages = [
        

        {"role": "system", "content": "You are a helpful assistant that identifies and resolves coreferences in text, providing standardized entity names."},
        {'role': 'user', 'content' : f"""
        In the following text, identify all entities (people, places, objects, etc.) and list their different mentions. Then, assign a unique standardized name to each entity, ensuring pronouns and possessive forms are correctly mapped.


        Text:
        \"\"\"
        {text}
        \"\"\"

        Output format:
        [
            {{
                "entity_id": "E1",
                "standard_name": "Standardized Entity Name",
                "mentions": ["First Mention", "Second Mention", ...]
            }},
            ...
        ]
        """}
    ]
    
    response = openai.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=messages,
      max_tokens=2000,
      temperature=0
  )
    return response.choices[0].message.content
