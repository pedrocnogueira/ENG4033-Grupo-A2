import rhythm
import melody
from midi_to_track_list import midi_to_track_list
from track_to_abc import track_to_abc
from abc_to_track import abc_to_track

from Track import Track


def perform_music_adjustments(track: Track, quantize: str | int = "AUTO", adjust_melody: bool = True) -> Track:
    resolution = 64
    if quantize == "AUTO":
        resolution = rhythm.suggest_resolution(track)
    elif type(quantize) == int:
        resolution = quantize
    
    track = rhythm.quantize(track, resolution=resolution)
    
    abc_track = track_to_abc(track, unit_note_length=resolution)

    if adjust_melody:
        abc_track = melody.correct_melody(abc_track)
    
    track = abc_to_track(abc_track, track.PPQ)
    return track

tracks = midi_to_track_list("midi/sample.mid", key="E")
track = tracks[1]

adjusted_track = perform_music_adjustments(track, quantize="AUTO", adjust_melody=True)
print(adjusted_track)
