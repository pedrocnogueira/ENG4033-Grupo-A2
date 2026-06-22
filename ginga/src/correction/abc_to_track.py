import re
from fractions import Fraction

from model.event import Event
from model.track import Track


_NOTE_TO_SEMITONE = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}


def _abc_note_to_midi(token: str) -> int:
    accidental = 1 if token.startswith("^") else 0

    if accidental:
        token = token

    letter = token[0]
    suffix = token[1:]

    if letter.islower():
        octave = 5 + suffix.count("'")
        letter = letter.upper()
    else:
        octave = 4 - suffix.count(",")
    
    midi = (octave + 1) * 12 + _NOTE_TO_SEMITONE[letter] + accidental
    return midi


def _parse_duration(duration_str: str, ticks_per_unit: float) -> int:
    if duration_str == "":
        frac = Fraction(1)
    elif duration_str.startswith("/"):
        frac = Fraction(1, int(duration_str[1:]))
    else:
        frac = Fraction(duration_str)

    return round(float(frac) * ticks_per_unit)


TOKEN_RE = re.compile(
    r"""
    (\[[^\]]+\]|z|\^?[A-Ga-g][',]*)
    ([0-9]+(?:/[0-9]+)?|/[0-9]+)?
    (-)?
    """,
    re.VERBOSE,
)   


def abc_to_track(abc: str, PPQ: int = 480) -> Track:
    lines = [line.strip() for line in abc.splitlines() if line.strip()]
    
    time_signature = (4, 4)
    unit_note_length = 16
    key = "C"
    
    body_lines = []

    for line in lines:
        if line.startswith("M:"):
            num, den = line[2:].split("/")
            time_signature = (int(num), int(den))
        elif line.startswith("L:"):
            _, den = line[2:].split("/")
            unit_note_length = int(den)
        elif line.startswith("K:"):
            key = line[2:]
        elif ":" not in line[:2]:
            body_lines.append(line)
    
    body = " ".join(body_lines)
    body = body.replace("|", " ")

    ticks_per_unit = PPQ * 4 / unit_note_length

    events: dict[int, list[Event]] = {}

    current_tick = 0

    pending_note = None
    pending_start = None
    pending_duration = 0

    for match in TOKEN_RE.finditer(body):
        token, length_str, tie = match.groups()

        duration = _parse_duration(length_str or "", ticks_per_unit)

        if token == "z":
            current_tick += duration
            continue

        if token.startswith("["):
            notes = re.findall(r"\^?[A-Ga-g][',]*", token)
            midi_notes = [_abc_note_to_midi(note) for note in notes]
        else:
            midi_notes = [_abc_note_to_midi(token)]
        
        if pending_note is not None:
            same_note = midi_notes == pending_note

            if same_note:
                pending_duration += duration

                if not tie:
                    events.setdefault(pending_start, []).extend( # type: ignore
                        Event(
                            type="note_on",
                            note=note,
                            duration=pending_duration,
                            velocity=80
                        )
                        for note in pending_note
                    )

                    pending_note = None
                    pending_start = None
                    pending_duration = 0
            else:
                events.setdefault(pending_start, []).extend( # type: ignore
                    Event(
                        type="note_on",
                        note=note,
                        duration=pending_duration,
                        velocity=80
                    )
                    for note in pending_note
                )

                pending_note = midi_notes
                pending_start = current_tick
                pending_duration = duration
        else:
            if tie:
                pending_note = midi_notes
                pending_start = current_tick
                pending_duration = duration
            else:
                events.setdefault(current_tick, []).extend(
                    Event(
                        type="note_on",
                        note=note,
                        duration=duration,
                        velocity=80
                    )
                    for note in midi_notes
                )

        current_tick += duration

    if pending_note is not None:
        events.setdefault(pending_start, []).extend( # type: ignore
            Event(
                type="note_on",
                note=note,
                duration=pending_duration,
                velocity=80
            )
            for note in pending_note
        )
    
    return Track(
        key=key,
        time_signature=time_signature,
        PPQ=PPQ,
        events=events
    )
