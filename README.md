
# UnscriptedAdventures

UnscriptedAdventures is a text-based RPG game that leverages Large Language Models (LLMs) to deliver a dynamic, immersive experience. Players engage with a virtual Game Master (GM) and Non-Player Characters (NPCs) through a chatbot interface, making choices that directly influence the unfolding narrative. The application is built using FastAPI, a modern, high-performance web framework for building APIs with Python.

**Note:** UnscriptedAdventures is currently in Alpha development. Documentation updates are ongoing. The project remains actively developed, and contributions are welcome. If you wish to contribute, please create a Pull Request.

![UnscriptedAdventures Preview](https://raw.githubusercontent.com/dspencej/UnscriptedAdventures/main/images/social_preview.png)

## Features

- **Dynamic Storytelling:** A virtual GM driven by an LLM agent guides the story, adapting to player choices and actions in real-time.
- **Character Creation:** Customize your character with a variety of traits, professions, and backgrounds to suit your play style.
- **Engaging Interactions:** Communicate with NPCs and make decisions that influence the game's evolving storyline and outcomes.
- **Reward System:** An innovative system evaluates player engagement and adjusts the GM's strategy to keep the experience exciting.

## Getting Started

For detailed instructions, see the [Getting Started Guide](https://github.com/dspencej/UnscriptedAdventures/wiki/Getting-Started-Guide) in the Wiki.

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/dspencej/UnscriptedAdventures.git
   cd UnscriptedAdventures
   ```

2. **Create a Virtual Environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # For Windows, use `.venv\Scripts\activate`
   ```

3. **Install the Required Packages:**

   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. **Start the FastAPI Application with Uvicorn:**

   ```bash
   uvicorn app:app --reload
   ```

   The `--reload` flag enables auto-reloading, allowing the server to restart upon code changes. This is useful during development.

2. **Open Your Browser:**

   Visit `http://127.0.0.1:8000` in your web browser to start playing.

3. **Interactive API Documentation:**

   FastAPI provides interactive API documentation:

   - **Swagger UI:** Accessible at `http://127.0.0.1:8000/docs`
   - **ReDoc:** Accessible at `http://127.0.0.1:8000/redoc`

## Contributing

For guidelines on contributing, see the [How to Contribute](https://github.com/dspencej/UnscriptedAdventures/wiki/How-to-Contribute) section of the Wiki.

1. **Fork the repository** and clone it locally.
2. **Create a new branch** for your feature or bug fix.
3. **Make your changes** and commit them with clear and concise messages.
4. **Push your changes** to your forked repository.
5. **Create a Pull Request** to the main branch of the original repository.

## License

This project is licensed under the MIT License—see the [LICENSE](LICENSE) file for details.

## Contact

If you have any questions, feedback, or suggestions, feel free to join the [discussion](https://github.com/dspencej/UnscriptedAdventures/discussions) or open an [issue](https://github.com/dspencej/UnscriptedAdventures/issues/new).

For bug reports, you can use the [Bug Report Template](https://github.com/dspencej/UnscriptedAdventures/issues/new?assignees=&labels=&template=bug_report.md&title=Bug%3A). To suggest a feature, use the [Feature Request Template](https://github.com/dspencej/UnscriptedAdventures/issues/new?assignees=&labels=&template=feature_request.md&title=Feature+Request%3A).

---

Enjoy your next story in the world of UnscriptedAdventures!

![UnscriptedAdventures Preview](https://raw.githubusercontent.com/dspencej/UnscriptedAdventures/main/images/social_preview_2.png)
