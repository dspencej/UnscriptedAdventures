# agents.py

import os

from autogen.agentchat import ConversableAgent

import chromadb
from chromadb.utils import embedding_functions
from llm.llm_config import LLM_PROVIDER, llm_config

# If Opal is selected, define the CustomOpalModelClient
if LLM_PROVIDER == "opal":
    from types import SimpleNamespace

    import requests

    class CustomOpalModelClient:
        def __init__(self, config, **kwargs):
            print(f"CustomOpalModelClient config: {config}")
            self.model_name = config["model"]
            self.api_key = config["api_key"]
            self.api_url = config.get(
                "api_url", "https://opal.jhuapl.edu/v2/chat/completions"
            )
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self.max_tokens = config.get("max_tokens", 2048)
            self.is_cui = config.get("is_cui", False)
            self.accept_cui_tos = config.get("accept_cui_tos", True)
            print(f"Initialized Opal Model Client for model {self.model_name}")

        def create(self, params):
            messages = params.get("messages")
            n = params.get("n", 1)
            stream = params.get("stream", False)
            temperature = params.get("temperature", 1.0)
            top_p = params.get("top_p", 1.0)
            max_tokens = params.get("max_tokens", self.max_tokens)

            # Prepare the payload for the Opal API
            payload = {
                "model": self.model_name,
                "messages": messages,
                "n": n,
                "stream": stream,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "is_cui": self.is_cui,
                "accept_cui_tos": self.accept_cui_tos,
            }

            response = SimpleNamespace()
            response.choices = []
            response.model = self.model_name

            try:
                resp = requests.post(
                    self.api_url, headers=self.headers, json=payload, verify=False
                )
                resp.raise_for_status()
                data = resp.json()

                for choice in data.get("choices", []):
                    message = choice.get("message", {})
                    choice_ns = SimpleNamespace()
                    choice_ns.message = SimpleNamespace(
                        content=message.get("content"),
                        role=message.get("role"),
                        function_call=message.get("function_call", None),
                    )
                    response.choices.append(choice_ns)
                # Optionally, store usage data
                response.usage = data.get("usage", {})
            except Exception as e:
                print(f"Exception during API call: {e}")
                raise e

            return response

        def message_retrieval(self, response):
            """Retrieve the messages from the response."""
            choices = response.choices
            return [choice.message.content for choice in choices]

        def cost(self, response) -> float:
            """Calculate the cost of the response."""
            # Opal API might not provide cost information.
            response.cost = 0
            return 0

        @staticmethod
        def get_usage(response):
            # Returns a dict of prompt_tokens, completion_tokens, total_tokens, cost, model
            usage = response.usage if hasattr(response, "usage") else {}
            return usage


# Initialize ChromaDB client for the RuleExpertAgent
CHROMA_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "chromadb")
)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Initialize embedding model for retrieval
EMBEDDING_MODEL = (
    "all-MiniLM-L6-v2"  # Ensure it's the same as used in pdf_processing.py
)
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)


class RuleExpertAgent(ConversableAgent):
    def __init__(self, name, llm_config, chroma_client):
        super().__init__(
            name=name,
            system_message="""You are an expert on Dungeons & Dragons rules. You are fact-based and concise.
Your role is to check if the player's intended action is allowed according to the D&D rules and if the player is capable of performing it.
Provide a detailed response indicating whether the action is permitted and any relevant rule explanations.""",
            llm_config=llm_config,
            code_execution_config=False,
        )
        self.description = (
            "Checks if the player's action is allowed according to D&D rules and determines if the player is capable of performing it.\n"
            "Returns whether the action is permitted along with relevant rule details.\n\n"
            "**Examples of messages:**\n"
            '- "I jump across the ravine."\n'
            '- "I attempt to fly without wings."\n'
            '- "I try to lift the giant boulder."\n'
        )
        self.chroma_client = chroma_client
        self.collection = self.chroma_client.get_collection(
            name="dnd_rules", embedding_function=embedding_function
        )

    def retrieve_rules(self, query):
        # Use ChromaDB to retrieve relevant documents
        results = self.collection.query(
            query_texts=[query],
            n_results=3,
        )
        # Combine retrieved documents
        retrieved_text = " ".join(
            [doc for docs in results["documents"] for doc in docs]
        )
        return retrieved_text

    def generate_reply(self, messages=None, sender=None, **kwargs):
        # Retrieve the last message content
        if messages:
            message_content = messages[-1]["content"]
        else:
            message_content = ""

        # Retrieve relevant rules
        rules_text = self.retrieve_rules(message_content)
        prompt = f"{message_content}\n\nRefer to the following rules:\n{rules_text}"

        # Generate reply using the base class's generate_reply method
        return super().generate_reply(
            messages=[{"role": "user", "content": prompt}], sender=sender, **kwargs
        )


class DMAgent(ConversableAgent):
    def __init__(self, name, llm_config):
        super().__init__(
            name=name,
            system_message="""You are the Dungeon Master in a text-based RPG.
Your role is to interpret the player's action along with the RuleExpertAgent's assessment.
- If the action is not permitted, inform the player why.
- If the action is allowed, summarize the action and coordinate with the StorytellerAgent for narrative progression.""",
            llm_config=llm_config,
            code_execution_config=False,
        )
        self.description = (
            "Interprets player actions in conjunction with the RuleExpertAgent's response.\n"
            "- Informs the player if an action is not permitted and explains why.\n"
            "- If allowed, prepares to advance the story by summarizing the action for the StorytellerAgent.\n\n"
            "**Examples of messages:**\n"
            '- "You cannot lift the boulder; it\'s too heavy."\n'
            '- "Player attempts to jump across the ravine."'
        )


class StorytellerAgent(ConversableAgent):
    def __init__(self, name, llm_config):
        super().__init__(
            name=name,
            system_message="""You are a storyteller responsible for enhancing the narrative.
Your task is to provide vivid descriptions based on the player's permitted actions, maintaining consistency and immersion.""",
            llm_config=llm_config,
            code_execution_config=False,
        )
        self.description = (
            "Provides immersive narrative descriptions for permitted player actions.\n"
            "Enhances the story while ensuring consistency and engagement.\n\n"
            "**Examples of messages:**\n"
            '- "As you leap across the ravine, the wind whistles past your ears..."\n'
            '- "The ancient door creaks open, revealing a hidden chamber..."'
        )


class AssistantAgent(ConversableAgent):
    def __init__(self, name, llm_config):
        super().__init__(
            name=name,
            system_message="""You handle all out-of-character (OOC) responses and messages that do not fit well with other specialized agents.
Your role includes:
- Providing direct responses to the player's OOC inputs.
- Handling general queries not specific to other agents.
- Maintaining the game's serious tone.""",
            llm_config=llm_config,
            code_execution_config=False,
        )
        self.description = (
            "Handles all out-of-character (OOC) communications and general inquiries.\n"
            "- Answers questions about game mechanics and setup.\n"
            "- Responds to meta-game questions or technical issues.\n\n"
            "**Examples of messages:**\n"
            '- "How do I create a character?"\n'
            '- "Can we pause the game?"'
        )


class RouterAgent(ConversableAgent):
    def __init__(self, name, llm_config):
        super().__init__(
            name=name,
            system_message="""You are responsible for routing messages between agents and the user.
Your role includes:
- Determining the next recipient (agent or user) of a message based on the sender, message content, and agent descriptions.
- Every message, whether from the user or another agent, should come to you first.
- You read who the message is from and what the content is, and then decide where it should go next.""",
            llm_config=llm_config,
            code_execution_config=False,
        )
        self.description = (
            "Routes messages between agents and the user based on the sender and message content.\n"
            "Utilizes agent descriptions and examples to make informed routing decisions.\n"
            "Ensures messages are directed appropriately in the message chain."
        )


# Instantiate agents

agents = {}

for agent_class in [
    RuleExpertAgent,
    DMAgent,
    StorytellerAgent,
    AssistantAgent,
    RouterAgent,
]:
    agent_name = agent_class.__name__
    if agent_name == "RuleExpertAgent":
        agent = agent_class(
            name=agent_name, llm_config=llm_config, chroma_client=chroma_client
        )
    else:
        agent = agent_class(
            name=agent_name,
            llm_config=llm_config,
        )
    if LLM_PROVIDER == "opal":
        # Register the CustomOpalModelClient with each agent
        agent.register_model_client(model_client_cls=CustomOpalModelClient)
    agents[agent_name] = agent

# Access agents as needed, for example:
rule_expert_agent = agents["RuleExpertAgent"]
dm_agent = agents["DMAgent"]
storyteller_agent = agents["StorytellerAgent"]
assistant_agent = agents["AssistantAgent"]
router_agent = agents["RouterAgent"]
