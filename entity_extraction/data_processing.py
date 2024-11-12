# entity_extraction/data_processing.py

import re
import textwrap
import json
from typing import List, Tuple
from .openai_integration import extract_relations, resolve_coreferences

def remove_text_after_options(text: str) -> str:
    """
    Removes text after the 'Options:' section.
    """
    pattern = r"(?s)(.*?)Options:.*"
    match = re.match(pattern, text)
    if match:
        return match.group(1).strip()
    return text

def merge_texts(text_list: List[str]) -> str:
    """
    Merges multiple texts after cleaning them.
    """
    cleaned_texts = [remove_text_after_options(text) for text in text_list]
    merged_corpus = "\n\n".join(cleaned_texts)
    return merged_corpus

def format_text(corpus: str, max_width: int = 80) -> str:
    """
    Formats text to ensure each line does not exceed max_width.
    """
    paragraphs = corpus.split('\n\n')
    wrapped_paragraphs = [textwrap.fill(paragraph, width=max_width) for paragraph in paragraphs]
    return "\n\n".join(wrapped_paragraphs)

def parse_triplets(input_text: str) -> List[Tuple[str, str, str]]:
    """
    Parses triplets from the extracted relations text.
    """
    triplets = []
    lines = input_text.strip().split('\n')
    pattern = re.compile(r'\((.*?)\)')
    
    for line in lines:
        match = pattern.search(line)
        if match:
            contents = match.group(1).split(',')
            contents = [element.strip() for element in contents]
            num_elements = len(contents)
            
            if num_elements == 3:
                triplet = tuple(contents)
            elif num_elements > 3:
                subject = contents[0]
                predicate = contents[-2]
                obj = contents[-1]
                descriptors = contents[1:-2]
                if descriptors:
                    subject = f"{subject}, " + ", ".join(descriptors)
                triplet = (subject, predicate, obj)
            else:
                print(f"Warning: Unexpected format in line: {line}")
                continue
            
            triplets.append(triplet)
        else:
            print(f"Warning: No parentheses found in line: {line}")
    
    return triplets

def process_texts_to_entities_and_triplets(texts: List[str]):
    """
    Processes multiple texts to extract and standardize entities and triplets.
    
    Returns:
        entity_dict: Dictionary mapping entities to unique IDs.
        standardized_triplets: List of standardized triplet tuples.
    """
    merged_text = merge_texts(texts)
    formatted_text = format_text(merged_text)
    #print(f"here is the formatted text\n {formatted_text}")
    # Extract relations
    raw_triplets_text = extract_relations(formatted_text)
    triplets = parse_triplets(raw_triplets_text)
    
    # Resolve coreferences
    coreferences_json = resolve_coreferences(merged_text)
    coreference_data = json.loads(coreferences_json)
    
    # Standardize triplets
    standardized_triplets = standardize_triplets(triplets, coreference_data)
    
    # Build entity dictionary
    entity_dict = build_entity_dict(standardized_triplets)
    
    return entity_dict, standardized_triplets

def standardize_triplets(triplets: List[Tuple[str, str, str]], coreference_data: List[dict]) -> List[Tuple[str, str, str]]:
    """
    Standardizes triplets using coreference data.
    """
    entity_map = {}
    for entity in coreference_data:
        standard_name = entity['standard_name']
        for mention in entity['mentions']:
            entity_map[mention.lower()] = standard_name
    
    standardized = []
    for head, relation, tail in triplets:
        head_std = entity_map.get(head.lower(), head)
        tail_std = entity_map.get(tail.lower(), tail)
        standardized.append((head_std, relation, tail_std))
    
    return standardized

def build_entity_dict(standardized_triplets: List[Tuple[str, str, str]]) -> dict:
    """
    Builds a dictionary mapping each unique entity to a unique ID.
    """
    entity_set = set()
    for head, _, tail in standardized_triplets:
        entity_set.add(head)
        entity_set.add(tail)
    entity_list = sorted(entity_set)  # Sorting for consistency
    entity_dict = {entity: f"E{idx+1}" for idx, entity in enumerate(entity_list)}
    return entity_dict
