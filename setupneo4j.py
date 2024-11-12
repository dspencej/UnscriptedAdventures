import os
import time
from neo4j import GraphDatabase

NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Neo4jPassword123")

def ping_neo4j(uri,user,password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    while True:
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            print("Neo4j is up and running.")
            break
        except Exception as e:
            print("You might need to start the Docker container or check your signin credentials!\nWaiting for Neo4j to start...")
            time.sleep(5)
    driver.close()

if __name__ == "__main__":
    ping_neo4j(NEO4J_URI,NEO4J_USER,NEO4J_PASSWORD)
    # setup logic passed
    print("Running setup...")

