
# UnscriptedAdventures

UnscriptedAdventures is a text-based RPG game that harnesses the power of Large Language Model (LLM) agents to deliver a dynamic, immersive experience. Players engage with a virtual Game Master (GM) and diverse Non-Player Characters (NPCs) through a chatbot interface, making choices that directly influence the unfolding narrative.

**Note: UnscriptedAdventures is currently in Alpha development.**

![UnscriptedAdventures Preview](https://raw.githubusercontent.com/dspencej/UnscriptedAdventures/refs/heads/main/images/social_preview.png)

## Features

- **Dynamic Storytelling:** A virtual GM driven by an LLM agent guides the story, adapting to player choices and actions in real-time.
- **Character Creation:** Customize your character with a variety of traits, professions, and backgrounds to suit your play style.
- **Engaging Interactions:** Communicate with NPCs and make decisions that influence the game's evolving storyline and outcomes.
- **Reward System:** An innovative system that evaluates player engagement and adjusts the GM's strategy to keep the experience exciting.
  
## Getting Started

### Prerequisites

- **Docker & Docker Compose:** Ensure you have Docker and Docker Compose installed on your machine.
- **Python 3.6+** (if you prefer running the application without Docker)
- **Environment Variables:** Create a `.env` file in the project root to store sensitive information.


For detailed instructions, see the [Getting Started Guide](https://github.com/dspencej/UnscriptedAdventures/wiki/Getting-Started-Guide) in the Wiki.

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/dspencej/UnscriptedAdventures.git
   cd UnscriptedAdventures
   ```


2. **Set Up Environment Variables:**
   Create a .env file in the project root with the following content:

   *env*
      NEO4J_PASSWORD=YourNeo4jPassword
      OPENAI_API_KEY=YourOpenAIAPIKey
   Note: Replace YourNeo4jPassword and YourOpenAIAPIKey with your actual credentials. Neo4jpassword check docker compose file

3. **Start the Services:**

   *bash*
      docker-compose up --build

4. **Create a Virtual Environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # For Windows, use `.venv\Scripts\activate`
   ```

5. **Install the Required Packages:**

   ```bash
   pip install -r requirements.txt
   ```

6. **Start Neo4j Database:**

   You can run Neo4j using Docker or install it locally.

   Using Docker:

   bash
      docker run \
      --name neo4j \
      -p 7474:7474 -p 7687:7687 \
      -d \
      -e NEO4J_AUTH=neo4j/YourNeo4jPassword \
      neo4j:4.4
   Note: Replace YourNeo4jPassword with your actual password.

### Running the Application

1. **Start the Flask Development Server:**

   ```bash
   flask run
   ```

2. **Open Your Browser:**

   Visit `http://127.0.0.1:5000` in your web browser to start playing!

## Contributing

For guidelines on contributing, see the [How to Contribute](https://github.com/dspencej/UnscriptedAdventures/wiki/How-to-Contribute) section of the Wiki.

1. **Fork the repository** and clone it locally.
2. **Create a new branch** for your feature or bug fix.
3. **Make your changes** and commit them with clear and concise messages.
4. **Push your changes** to your forked repository.
5. **Create a Pull Request** to the main branch of the original repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

If you have any questions, feedback, or suggestions, feel free to join the [discussion](https://github.com/dspencej/UnscriptedAdventures/discussions) or open an [issue](https://github.com/dspencej/UnscriptedAdventures/issues/new).

For bug reports, you can use the [Bug Report Template](https://github.com/dspencej/UnscriptedAdventures/issues/new?assignees=&labels=&template=bug_report.md&title=Bug%3A). To suggest a feature, use the [Feature Request Template](https://github.com/dspencej/UnscriptedAdventures/issues/new?assignees=&labels=&template=feature_request.md&title=Feature+Request%3A).

---

Enjoy your next story in the world of UnscriptedAdventures!

![UnscriptedAdventures Preview](https://raw.githubusercontent.com/dspencej/UnscriptedAdventures/refs/heads/main/images/social_preview_2.png)
