import subprocess
import platform
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

# Access the variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def find_docker_compose_directory():
    """
    Placeholder function to locate the docker-compose directory.
    Implement this function based on your project's structure.
    """
    # Example implementation:
    return os.path.dirname(os.path.abspath(__file__))

def start_docker_daemon(os_type):
    """
    Attempts to start the Docker daemon based on the operating system.
    """
    if os_type == "Linux":
        try:
            print("Attempting to start Docker daemon on Linux...")
            subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
            print("Docker daemon started successfully on Linux.")
        except subprocess.CalledProcessError as daemon_error:
            print(f"Failed to start Docker daemon on Linux: {daemon_error}")
    elif os_type == "Darwin":
        try:
            print("Attempting to start Docker Desktop on macOS...")
            subprocess.run(["open", "-a", "Docker"], check=True)
            print("Docker Desktop is opening on macOS.")
        except subprocess.CalledProcessError as daemon_error:
            print(f"Failed to open Docker Desktop on macOS: {daemon_error}")
    elif os_type == "Windows":
        try:
            print("Attempting to start Docker Desktop on Windows...")
            subprocess.run(["start", "Docker"], shell=True, check=True)
            print("Docker Desktop is starting on Windows.")
        except subprocess.CalledProcessError as daemon_error:
            print(f"Failed to start Docker Desktop on Windows: {daemon_error}")
    else:
        print("Unsupported operating system. Please start the Docker daemon manually.")

def ping_neo4j(uri, user, password, max_retries=3, retry_interval=5):
    """
    Pings the Neo4j database and ensures that the Docker containers are running.

    Args:
        uri (str): The URI of the Neo4j instance.
        user (str): Username for Neo4j authentication.
        password (str): Password for Neo4j authentication.
        max_retries (int): Maximum number of retry attempts.
        retry_interval (int): Seconds to wait between retries.
    """
    docker_compose_dir = find_docker_compose_directory()
    driver = GraphDatabase.driver(uri, auth=(user, password))
    retries = 0

    while retries < max_retries:
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            print("✅ Neo4j is up and running.")
            driver.close()
            return  # Exit the function upon successful connection
        except Exception as e:
            print(f"⚠️ Neo4j is not running (Attempt {retries + 1}/{max_retries}). Error: {e}")
            print("🔄 Attempting to start Docker containers using docker compose...")
            try:
                # Run docker compose up -d
                subprocess.run(["docker", "compose", "up", "-d"], cwd=docker_compose_dir, check=True)
                print("🚀 Docker containers are being started. Retrying connection...")
            except subprocess.CalledProcessError as docker_error:
                print(f"❌ Failed to start Docker containers: {docker_error}")
                print("🔧 Attempting to start the Docker daemon manually...")

                # Determine the operating system
                os_type = platform.system()
                print(f"🖥️ Detected OS type: {os_type}")

                # Attempt to start the Docker daemon based on OS
                start_docker_daemon(os_type)

                print("⏳ Waiting for the Docker daemon to initialize...")
                time.sleep(10)  # Wait longer to ensure Docker daemon starts

                # Retry running docker compose up -d after starting the daemon
                try:
                    print("🔄 Retrying to start Docker containers using docker compose...")
                    subprocess.run(["docker", "compose", "up", "-d"], cwd=docker_compose_dir, check=True)
                    print("🚀 Docker containers are being started after daemon initialization.")
                except subprocess.CalledProcessError as retry_error:
                    print(f"❌ Retry failed to start Docker containers: {retry_error}")

        retries += 1
        if retries < max_retries:
            print(f"⏳ Waiting for {retry_interval} seconds before next attempt...")
            time.sleep(retry_interval)
        else:
            print("❗ Maximum retry attempts reached. Please check your Docker and Neo4j configurations.")
            driver.close()


if __name__ == "__main__":
    try:
        ping_neo4j(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    except FileNotFoundError as e:
        print(str(e))

