# UnscriptedAdventures

UnscriptedAdventures is a text-based RPG game that leverages Large Language Model (LLM) agents to create a dynamic and immersive experience. Players interact with a virtual Game Master (GM) and various Non-Player Characters (NPCs) through a chatbot interface, making choices that shape the narrative.

![UnscriptedAdventures Preview](https://github.com/dspencej/UnscriptedAdventures/blob/main/images/social_preview.png)

## Features

- **Dynamic Storytelling:** A virtual GM driven by an LLM agent guides the story, adapting to player choices and actions in real-time.
- **Character Creation:** Customize your character with a variety of traits, professions, and backgrounds to suit your play style.
- **Engaging Interactions:** Communicate with NPCs and make decisions that influence the game's evolving storyline and outcomes.
- **Reward System:** An innovative system that evaluates player engagement and adjusts the GM's strategy to keep the experience exciting.
  
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
- `images/`: Contains all image resources.

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

If you have any questions, feedback, or suggestions, feel free to join the [discussion](https://github.com/dspencej/UnscriptedAdventures/discussions) or open an [issue](https://github.com/dspencej/UnscriptedAdventures/issues/new).

---

Enjoy your next story in the world of UnscriptedAdventures!

![UnscriptedAdventures Preview](https://github.com/dspencej/UnscriptedAdventures/blob/main/images/social_preview_2.png)
