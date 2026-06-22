from dataclasses import dataclass

@dataclass
class Event:
    def __init__(self, type: str, note: int, duration: int, channel: int = 0, velocity: int = 0):
        self.type = type
        self.note = note
        self.duration = duration
        self.channel = channel
        self.velocity = velocity

    type: str
    note: int
    duration: int
    channel: int
    velocity: int
