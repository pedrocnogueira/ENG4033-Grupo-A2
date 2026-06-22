import ginga.src.correction.llm as llm

from model.track import Track

def correct_melody(abc: str) -> str:
    full_prompt = ""
    with open("prompts/melody_prompt.txt", 'r') as prompt_file:
        full_prompt = prompt_file.read()
    full_prompt += abc
    response = llm.send_message(full_prompt)
    return response
