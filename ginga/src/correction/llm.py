from ollama import chat
from ollama import ChatResponse

MODEL = 'gemma3'

def send_message(message: str) -> str:
    response: ChatResponse = chat(
        model=MODEL,
        messages=[{'role': 'user', 'content': message}],
        options={'temperature': 0.2}
    )
    return response.message.content or ""
