# entity_extraction/__init__.py

from .data_processing import process_texts_to_entities_and_triplets, merge_texts, format_text
from .openai_integration import extract_relations, resolve_coreferences
from .neo4j_integration import write_to_database, list_entities_and_relationships, get_graph_data, close_driver
from .utils import print_formatted_text

__all__ = [
    "process_texts_to_entities_and_triplets",
    "merge_texts",
    "format_text",
    "extract_relations",
    "resolve_coreferences",
    "write_to_database",
    "list_entities_and_relationships",
    "get_graph_data",
    "close_driver",
    "print_formatted_text",
    "format_graph_data",
    "retrieve_relevant_information"
]
