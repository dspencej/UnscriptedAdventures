import os
import time
import subprocess
import platform

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Access the variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def find_docker_compose_directory():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    while current_dir != os.path.dirname(current_dir):  # Stop when reaching the root directory
        if "docker-compose.yml" in os.listdir(current_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    raise FileNotFoundError("docker-compose.yml not found in any parent directory.")

def ping_neo4j(uri, user, password):
    docker_compose_dir = find_docker_compose_directory()
    driver = GraphDatabase.driver(uri, auth=(user, password))
    while True:
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            print("Neo4j is up and running.")
            break
        except Exception as e:
            print("Neo4j is not running. Attempting to start Docker container...")
            try:
                # Run docker compose up -d
                subprocess.run(["docker", "compose", "up", "-d"], cwd=docker_compose_dir, check=True)
                print("Docker containers are being started. Retrying connection...")
            except subprocess.CalledProcessError as docker_error:
                print(f"Failed to start Docker containers: {docker_error}\n Start the docker daemon ")

                # Determine the operating system
                os_type = platform.system()
                print(f'OS type: {os_type}')
                
                if os_type == "Linux":
                    try:
                        # Attempt to start Docker daemon using systemctl
                        subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
                        print("Docker daemon started successfully.")
                    except subprocess.CalledProcessError as daemon_error:
                        print(f"Failed to start Docker daemon on Linux: {daemon_error}")
                
                elif os_type == "Darwin":
                    try:
                        # Attempt to open Docker Desktop on macOS
                        subprocess.run(["open", "-a", "Docker"], check=True)
                        print("Docker Desktop is opening.")
                    except subprocess.CalledProcessError as daemon_error:
                        print(f"Failed to open Docker Desktop on macOS: {daemon_error}")
                
                elif os_type == "Windows":
                    try:
                        # Attempt to start Docker Desktop on Windows
                        subprocess.run(["start", "Docker"], shell=True, check=True)
                        print("Docker Desktop is starting.")
                    except subprocess.CalledProcessError as daemon_error:
                        print(f"Failed to start Docker Desktop on Windows: {daemon_error}")
                
                else:
                    print("Unsupported operating system. Please start the Docker daemon manually.")
            time.sleep(5)

            break
    driver.close()

if __name__ == "__main__":
    try:
        ping_neo4j(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        print("Running setup...")
    except FileNotFoundError as e:
        print(str(e))
