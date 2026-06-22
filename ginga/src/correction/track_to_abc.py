import math
from fractions import Fraction

from model.event import Event
from model.track import Track


_PITCH_NAMES = {
    0: ("C", ""),
    1: ("C", "^"),
    2: ("D", ""),
    3: ("D", "^"),
    4: ("E", ""),
    5: ("F", ""),
    6: ("F", "^"),
    7: ("G", ""),
    8: ("G", "^"),
    9: ("A", ""),
    10: ("A", "^"),
    11: ("B", ""),
}


def _midi_note_to_abc(note: int) -> str:
    if not (0 <= note <= 127):
        raise ValueError(f"MIDI note {note} out of range (0-127)")
    
    chromatic = (note - 60) % 12
    octave = note // 12 - 1

    letter, accidental = _PITCH_NAMES[chromatic]

    if octave >= 5:
        letter = letter.lower()
        suffix = "'" * (octave - 5)
    else:
        suffix = "," * (4 - octave)
    
    return accidental + letter + suffix


def _format_duration(ticks: int, ticks_per_unit: float) -> str:
    frac = Fraction(ticks / ticks_per_unit).limit_denominator(64)
    if frac <= 0:
        frac = Fraction(1)
    if frac == 1:
        return ""
    if frac.denominator == 1:
        return str(frac.numerator)
    if frac.numerator == 1:
        return f"/{frac.denominator}"
    return f"{frac.numerator}/{frac.denominator}"


def _build_timeline(track: Track, ticks_per_measure: int) -> list[tuple[int, str]]:
    timeline: list[tuple[int, str]] = []

    sorted_ticks = sorted(track.events.keys())

    last_tick = max(
        start_tick + max(event.duration for event in events) 
        for start_tick, events in track.events.items()
    )

    n_measures = math.ceil(last_tick / ticks_per_measure)
    end_tick = n_measures * ticks_per_measure

    cursor = 0

    for tick in sorted_ticks:
        if tick < cursor:
            # Overlapping note (polyphony): skip
            continue

        events = track.events[tick]
        duration = max(event.duration for event in events)

        if tick > cursor:
            # Gap before this event → rest
            timeline.append((tick - cursor, 'z'))
        
        if len(events) == 1:
            token = _midi_note_to_abc(events[0].note)
        else:
            token = '[' + ''.join(_midi_note_to_abc(event.note) for event in events) + ']'

        timeline.append((duration, token))
        cursor = tick + duration
    
    if cursor < end_tick:
        timeline.append((end_tick - cursor, 'z'))
    
    return timeline


def _build_body_parts(timeline: list[tuple[int, str]], ticks_per_unit: float, ticks_per_measure: int) -> list[str]:
    body_parts: list[str] = []

    measure_ticks = 0

    for duration, token in timeline:
        remaining = duration

        while remaining > 0:
            space = ticks_per_measure - measure_ticks
            chunk = min(remaining, space)
            will_split = remaining > space
            length_str = _format_duration(chunk, ticks_per_unit)

            tie = '-' if (will_split and token != 'z') else ''
            body_parts.append(f"{token}{length_str}{tie}")

            measure_ticks += chunk
            remaining -= chunk

            if measure_ticks >= ticks_per_measure:
                body_parts.append('|')
                measure_ticks = 0
    
    return body_parts


def track_to_abc(track: Track, title: str = "Untitled", unit_note_length: int = 16) -> str:
    num, den = track.time_signature

    ticks_per_unit = track.PPQ * 4 / unit_note_length
    ticks_per_measure = track.PPQ * 4 * num // den

    header = (
        f"X:1\n"
        f"T:{title}\n"
        f"M:{num}/{den}\n"
        f"L:1/{unit_note_length}\n"
        f"K:{track.key}\n"
    )

    if not track.events:
        empty = _format_duration(ticks_per_measure, ticks_per_unit)
        return header + f"z{empty}|\n"
    
    timeline = _build_timeline(track, ticks_per_measure)

    body_parts = _build_body_parts(timeline, ticks_per_unit, ticks_per_measure)

    return header + ' '.join(body_parts) + "\n"
