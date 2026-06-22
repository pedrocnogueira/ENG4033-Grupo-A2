import mido
from collections import defaultdict

from Event import Event
from Track import Track

def midi_to_track_list(input_path: str, key: str = "C") -> list[Track]:
    midi = mido.MidiFile(input_path)
    ppq = midi.ticks_per_beat
    time_signature = (4, 4)

    tracks: list[Track] = []

    for track in midi.tracks:
        tick = 0
        events: dict[int, list[Event]] = defaultdict(list)
        pending: dict[tuple[int, int], tuple[int, Event]] = {}

        for msg in track:
            tick += msg.time

            if msg.is_meta:
                if msg.type == "time_signature":
                    time_signature = (msg.numerator, msg.denominator)
                continue

            is_note_on = msg.type == "note_on" and msg.velocity > 0
            is_note_off = msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0)

            if is_note_on:
                pending[(msg.channel, msg.note)] = (tick, msg)
            elif is_note_off:
                pending_key = (msg.channel, msg.note)
                if pending_key in pending:
                    start_tick, event_msg = pending.pop(pending_key)
                    new_event = Event(
                        type=event_msg.type,
                        note=event_msg.note,
                        duration=tick - start_tick,
                        channel=event_msg.channel,
                        velocity=event_msg.velocity
                    )
                    events[start_tick].append(new_event)

        new_track = Track(
            key=key,
            time_signature=time_signature, 
            PPQ=ppq, 
            events=events
        )
        tracks.append(new_track)

    return tracks
