from ollama import AsyncClient


# Function to generate a response using Ollama's LLM asynchronously
async def generate_gm_response(prompt):
    try:
        message = {'role': 'user', 'content': prompt}
        client = AsyncClient()
        response = await client.chat(model='mistral:v0.3', messages=[message])
        return response['message']['content']
    except Exception as e:
        return f"Error generating response: {e}"


# Function to handle streaming responses from Ollama's LLM
async def generate_gm_response_stream(prompt):
    try:
        message = {'role': 'user', 'content': prompt}
        client = AsyncClient()
        response_stream = client.chat(model='mistral:v0.3', messages=[message], stream=True)
        response_content = ""

        async for part in response_stream:
            response_content += part['message']['content']
        return response_content
    except Exception as e:
        return f"Error generating response: {e}"
