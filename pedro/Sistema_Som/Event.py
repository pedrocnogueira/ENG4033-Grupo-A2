from dataclasses import dataclass


@dataclass
class Event:
    type: str = "note_on"
    note: int
    duration: int
    channel: int = 0
    velocity: int = 0
