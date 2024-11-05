from neo4j import GraphDatabase
import os

def setup_database(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        # Example: Create uniqueness constraints
        constraints = [
            "CREATE CONSTRAINT unique_story_id IF NOT EXISTS FOR (n:Story) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT unique_character_id IF NOT EXISTS FOR (n:Character) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT unique_location_id IF NOT EXISTS FOR (n:Location) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT unique_item_id IF NOT EXISTS FOR (n:Item) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT unique_event_id IF NOT EXISTS FOR (n:Event) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT unique_quest_id IF NOT EXISTS FOR (n:Quest) REQUIRE n.id IS UNIQUE"
        ]

        for constraint in constraints:
            try:
                session.run(constraint)
                print(f"Executed Constraint: {constraint}")
            except Exception as e:
                print(f"Failed to execute constraint: {constraint}\nError: {e}")

    driver.close()

if __name__ == "__main__":
    neo4j_uri = "neo4j://localhost:7687"  # Bolt URI
    neo4j_user = "neo4j"
    neo4j_password = os.getenv("NEO4J_PASSWORD", "Neo4jPassword123")  # Use environment variable

    setup_database(neo4j_uri, neo4j_user, neo4j_password)
