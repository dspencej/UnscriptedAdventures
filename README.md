# UnscriptedAdventures

UnscriptedAdventures is a text-based RPG game inspired by Dungeons & Dragons (D&D). The game leverages Large Language Model (LLM) agents to create a dynamic and immersive experience where players interact with a Dungeon Master (DM) and various Non-Player Characters (NPCs) through a chatbot interface.

## Features

- **Dynamic Storytelling:** A virtual DM driven by an LLM agent guides the story, responding to player choices and actions.
- **Character Creation:** Create and customize your character with various races, classes, and backgrounds.
- **Engaging Interactions:** Communicate with NPCs and make choices that influence the game's storyline and outcome.
- **Reward System:** A unique reward system that evaluates player engagement and adjusts the DM's strategy accordingly.

## Getting Started

### Prerequisites

- **Python 3.7+** is required.
- **Flask**: Install Flask using pip:

  ```bash
  pip install flask
  ```

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

1. **Start the Flask Development Server:**

   ```bash
   flask run
   ```

2. **Open Your Browser:**

   Visit `http://127.0.0.1:5000` in your web browser to start playing!

### Project Structure

- `app.py`: The main application file that runs the Flask server and handles routes.
- `templates/`: Contains all HTML templates (`index.html`, `about.html`, `contact.html`, etc.)
- `static/`: Contains static files like `styles.css`.
- `characters.json`: Stores the character data for the game.
- `.gitignore`: Lists files and directories to be ignored by Git (e.g., `.idea/`).

## Contributing

We welcome contributions to UnscriptedAdventures! Here’s how you can help:

1. **Fork the repository** and clone it locally.
2. **Create a new branch** for your feature or bug fix.
3. **Make your changes** and commit them with clear and concise messages.
4. **Push your changes** to your forked repository.
5. **Create a Pull Request** to the main branch of the original repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

If you have any questions, feedback, or suggestions, feel free to reach out via the [Contact Page](http://127.0.0.1:5000/contact) or open an issue on GitHub.

---

Enjoy your adventures in the world of UnscriptedAdventures!
