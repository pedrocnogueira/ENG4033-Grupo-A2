from dataclasses import dataclass


@dataclass
class Event:
    note: int
    duration: int
    channel: int = 0
    velocity: int = 0
    type: str = "note_on"
