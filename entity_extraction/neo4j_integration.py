# entity_extraction/neo4j_integration.py

from neo4j import GraphDatabase
from typing import List, Tuple

import os

# Load Neo4j credentials from environment variables or a config file
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Neo4jPassword123")

if not NEO4J_PASSWORD:
    raise ValueError("Neo4j password not found. Please set the NEO4J_PASSWORD environment variable.")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def capitalize_name(name: str) -> str:
    
    if not name:
        return name
    return name[0].upper() + name[1:]


def retrieve_relevant_information():
    with driver.session() as session:
        # query to retrieve relevant data #tweak to taste
        result = session.run("""
            MATCH (n:Entity)-[r]->(m:Entity)
            RETURN n.name AS source, type(r) AS relation, m.name AS target
        """)
        data = []
        for record in result:
            data.append({
                'source': record['source'],
                'relation': record['relation'],
                'target': record['target']
            })
    return data


def create_nodes(tx, entity_dict: dict):
    for name, eid in entity_dict.items():
        capitalized_name = capitalize_name(name)
        # Check if entity already exists
        result = tx.run("MATCH (n:Entity {name: $name}) RETURN n.id AS id", name=capitalized_name)
        record = result.single()
        if record:
            # Entity exists, update the entity_dict to use existing ID
            existing_id = record["id"]
            entity_dict[name] = existing_id
        else:
            # Create new entity
            tx.run(
                "CREATE (n:Entity {id: $id, name: $name})",
                id=eid,
                name=capitalized_name
            )

def create_relationships(tx, standardized_triplets: List[Tuple[str, str, str]], entity_dict: dict):
    for head, relation, tail in standardized_triplets:
        source_id = entity_dict[head]
        target_id = entity_dict[tail]
        tx.run(
            "MATCH (a:Entity {id: $source_id}), (b:Entity {id: $target_id}) "
            "MERGE (a)-[r:RELATIONSHIP {name: $relation}]->(b)",
            source_id=source_id,
            target_id=target_id,
            relation=relation
        )

def write_to_database(entity_dict: dict, standardized_triplets: List[Tuple[str, str, str]]):
    with driver.session() as session:
        session.write_transaction(create_nodes, entity_dict)
        session.write_transaction(create_relationships, standardized_triplets, entity_dict)
    print("Data successfully written to the Neo4j database.")

def list_entities_and_relationships():
    with driver.session() as session:
        # Retrieve all entities
        entities = session.run("MATCH (e:Entity) RETURN e.id AS id, e.name AS name")
        entity_dict = {}
        print("Entities:")
        for record in entities:
            entity_id = record["id"]
            name = record["name"]
            entity_dict[entity_id] = name
            print(f"  {entity_id}: {name}")
        
        print("\nRelationships:")
        # Retrieve all relationships
        relationships = session.run("""
            MATCH (a:Entity)-[r:RELATIONSHIP]->(b:Entity)
            RETURN a.id AS source_id, r.name AS relation, b.id AS target_id
        """)
        for record in relationships:
            source = entity_dict.get(record["source_id"], "Unknown")
            relation = record["relation"]
            target = entity_dict.get(record["target_id"], "Unknown")
            print(f"  ({source}) -[{relation}]-> ({target})")

def get_graph_data() -> dict:
    """
    Retrieves all Entity nodes and their RELATIONSHIP relationships from Neo4j.
    
    Returns:
        dict: Contains lists of entities and relationships.
    """
    entities = {}
    relationships = []

    with driver.session() as session:
        # Retrieve all entities
        entity_records = session.run("MATCH (e:Entity) RETURN e.id AS id, e.name AS name")
        for record in entity_records:
            entity_id = record["id"]
            name = record["name"]
            entities[entity_id] = name

        # Retrieve all relationships
        relationship_records = session.run("""
            MATCH (a:Entity)-[r:RELATIONSHIP]->(b:Entity)
            RETURN a.id AS source_id, r.name AS relation, b.id AS target_id
        """)
        for record in relationship_records:
            source_id = record["source_id"]
            relation = record["relation"]
            target_id = record["target_id"]
            relationships.append({
                "source": source_id,
                "relation": relation,
                "target": target_id
            })

    graph_data = {
        "entities": [{"id": eid, "name": name} for eid, name in entities.items()],
        "relationships": relationships
    }

    return graph_data

def reset_graph(driver):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n;")

def close_driver():
    driver.close()
