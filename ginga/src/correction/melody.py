from . import llm

from ..model.track import Track
from ..config import RAIZ


def correct_melody(abc: str) -> str:
    full_prompt = ""
    with open(str(RAIZ / "assets" / "prompts" / "melody_prompt.txt"), 'r') as prompt_file:
        full_prompt = prompt_file.read()
    full_prompt += abc
    response = llm.send_message(full_prompt)
    return response
