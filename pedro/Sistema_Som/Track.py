from dataclasses import dataclass, field

from .Event import Event


@dataclass
class Track:
    def __init__(self, key: str, time_signature: tuple[int, int] = (4, 4), 
                 PPQ: int = 480, events: dict[int, list[Event]] = {}):
        self.key = key
        self.time_signature = time_signature
        self.PPQ = PPQ
        self.events = events

    key: str
    time_signature: tuple[int, int]
    PPQ: int # ticks per quarter note
    events: dict[int, list[Event]]

    def __str__(self) -> str:
        s = f"Track: {self.key}\n"
        s += f"Time signature: {self.time_signature[0]}/{self.time_signature[1]}\n"
        s += f"Ticks per quarter note: {self.PPQ}\n"
        for tick, events in self.events.items():
            s += f"Tick {tick}:\n"
            for event in events:
                s += f"note: {event.note}, duration: {event.duration}\n"
        return s
