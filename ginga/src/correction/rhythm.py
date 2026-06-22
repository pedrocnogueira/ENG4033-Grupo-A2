import llm

from model.event import Event
from model.track import Track


def suggest_resolution(track: Track) -> int:
    full_prompt = ""
    with open("prompts/rhythm_prompt.txt", 'r') as prompt_file:
        full_prompt += prompt_file.read()
    full_prompt += track.__str__()
    response = llm.send_message(full_prompt)
    return int(response)


def quantize(track: Track, resolution: int = 4) -> Track:
    grid = 4 * track.PPQ / resolution

    quantized_events: dict[int, list[Event]] = {}
    for tick, events in list(track.events.items()):
        new_tick = int(round(tick / grid) * grid)
        for event in events:
            event.duration = int(round(event.duration / grid) * grid)
        
        if new_tick in quantized_events:
            quantized_events[new_tick].extend(events)
        else:
            quantized_events[new_tick] = events

    return Track(
        key=track.key,
        time_signature=track.time_signature, 
        PPQ=track.PPQ, 
        events=quantized_events
    )
