from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import mido
import pynbs

from pyhtsl.types import ALL_SOUNDS

from ..actions.pause_execution import PauseExecutionExpression
from ..actions.play_sound import PlaySoundExpression
from ..expression.expression import Expression

__all__ = (
    'NoteEvent',
    'music_into_note_events',
    'note_events_into_expressions',
    'music_into_expressions',
)


# NBS instrument ID -> Housing sound (raw)
# 0-6 are 1.8.9 vanilla, 7-15 are 1.12+ (mapped to closest 1.8.9 equivalent)
NBS_INSTRUMENT_TO_SOUND: dict[int, ALL_SOUNDS] = {
    0: 'note.harp',  # Piano
    1: 'note.bass',  # Double Bass
    2: 'note.bd',  # Bass Drum
    3: 'note.snare',  # Snare Drum
    4: 'note.hat',  # Click / Sticks
    5: 'note.bassattack',  # Guitar
    6: 'note.harp',  # Flute -> Piano
    7: 'note.pling',  # Bell -> Pling
    8: 'note.pling',  # Chime -> Pling
    9: 'note.pling',  # Xylophone -> Pling
    10: 'note.pling',  # Iron Xylophone -> Pling
    11: 'note.hat',  # Cow Bell -> Sticks
    12: 'note.bass',  # Didgeridoo -> Bass
    13: 'note.pling',  # Bit -> Pling
    14: 'note.bassattack',  # Banjo -> Guitar
    15: 'note.pling',  # Pling
}

# MIDI program number ranges -> Housing sound
MIDI_PROGRAM_TO_SOUND: dict[range, ALL_SOUNDS] = {
    range(0, 8): 'note.harp',  # Piano
    range(8, 16): 'note.pling',  # Chromatic Percussion
    range(16, 24): 'note.harp',  # Organ
    range(24, 32): 'note.bassattack',  # Guitar
    range(32, 40): 'note.bass',  # Bass
    range(40, 56): 'note.harp',  # Strings / Ensemble
    range(56, 64): 'note.harp',  # Brass
    range(64, 72): 'note.harp',  # Reed
    range(72, 80): 'note.harp',  # Pipe
    range(80, 88): 'note.pling',  # Synth Lead
    range(88, 96): 'note.harp',  # Synth Pad
    range(96, 104): 'note.pling',  # Synth Effects
    range(104, 112): 'note.bassattack',  # Ethnic
    range(112, 120): 'note.bd',  # Percussive
    range(120, 128): 'note.hat',  # Sound Effects
}

# MIDI drum note numbers (channel 10) -> Housing sound
MIDI_DRUM_TO_SOUND: dict[int, ALL_SOUNDS] = {
    35: 'note.bd',
    36: 'note.bd',  # Bass Drum
    38: 'note.snare',
    40: 'note.snare',  # Snare
    42: 'note.hat',
    44: 'note.hat',
    46: 'note.hat',  # Hi-Hat
}
MIDI_DRUM_DEFAULT = 'note.hat'


def _midi_program_to_sound(program: int) -> ALL_SOUNDS:
    for r, sound in MIDI_PROGRAM_TO_SOUND.items():
        if program in r:
            return sound
    return 'note.harp'


def _nbs_key_to_pitch(
    key: float,
    *,
    clamp_pitch: bool = True,
) -> float:
    """Convert NBS key (0-87, fractional for fine-tuning) to Housing pitch (0.0-2.0).

    Key 33 = F#3 -> 0.0, Key 45 = F#4 -> 1.0, Key 57 = F#5 -> 2.0
    """
    pitch = (key - 33) / 12
    if clamp_pitch:
        pitch = max(0.0, min(2.0, pitch))
    return pitch


def _midi_note_to_pitch(
    note: int,
    *,
    clamp_pitch: bool = True,
) -> float:
    """Convert MIDI note (0-127) to Housing pitch (0.0-2.0).

    MIDI 21 = A0 = NBS key 0, so nbs_key = midi_note - 21.
    """
    return _nbs_key_to_pitch(note - 21, clamp_pitch=clamp_pitch)


@dataclass
class NoteEvent:
    housing_tick: int
    sound: ALL_SOUNDS
    volume: float
    pitch: float


def note_events_into_expressions(
    events: list[NoteEvent],
    *,
    strip_pauses: bool = True,
    sound_factory: Callable[[NoteEvent], PlaySoundExpression] | None = None,
    sound_transform: Callable[[PlaySoundExpression], PlaySoundExpression | None]
    | None = None,
    sound_filter: Callable[[PlaySoundExpression], bool] | None = None,
) -> list[Expression]:
    events.sort(key=lambda e: e.housing_tick)
    result: list[Expression] = []
    current_tick = 0
    for i, event in enumerate(events):
        delta = event.housing_tick - current_tick
        if delta > 0:
            if not (strip_pauses and i == 0):
                result.append(PauseExecutionExpression(ticks=delta))
            current_tick = event.housing_tick
        if sound_factory is not None:
            expr = sound_factory(event)
        else:
            expr = PlaySoundExpression(
                sound=event.sound,
                volume=event.volume,
                pitch=event.pitch,
                check_valid=False,
            )
        if sound_transform is not None:
            expr = sound_transform(expr) or expr
        result.append(expr)

    if sound_filter is not None:
        filtered: list[Expression] = []
        pending_ticks = 0
        for expr in result:
            if isinstance(expr, PauseExecutionExpression):
                pending_ticks += expr.ticks
                continue
            if isinstance(expr, PlaySoundExpression) and not sound_filter(expr):
                continue
            if pending_ticks > 0:
                filtered.append(PauseExecutionExpression(ticks=pending_ticks))
                pending_ticks = 0
            filtered.append(expr)
        if pending_ticks > 0:
            filtered.append(PauseExecutionExpression(ticks=pending_ticks))
        result = filtered

    if strip_pauses:
        while result and isinstance(result[-1], PauseExecutionExpression):
            result.pop()
        while result and isinstance(result[0], PauseExecutionExpression):
            result.pop(0)

    return result


def _events_from_nbs(
    path: Path,
    *,
    clamp_pitch: bool = True,
) -> list[NoteEvent]:
    song = pynbs.read(str(path))
    tps = song.header.tempo
    events: list[NoteEvent] = []

    layer_volumes: dict[int, float] = {}
    for i, layer in enumerate(song.layers):
        layer_volumes[i] = layer.volume / 100

    for tick, chord in song:
        housing_tick = round(tick * 20 / tps)
        for note in chord:
            sound = NBS_INSTRUMENT_TO_SOUND.get(note.instrument, 'note.harp')
            layer_vol = layer_volumes.get(note.layer, 1.0)
            volume = (note.velocity / 100) * layer_vol
            pitch = _nbs_key_to_pitch(
                note.key + note.pitch / 100,
                clamp_pitch=clamp_pitch,
            )
            events.append(
                NoteEvent(
                    housing_tick=housing_tick,
                    sound=sound,
                    volume=volume,
                    pitch=pitch,
                )
            )

    return events


def _events_from_midi(
    path: Path,
    *,
    clamp_pitch: bool = True,
) -> list[NoteEvent]:
    mid = mido.MidiFile(str(path))
    events: list[NoteEvent] = []
    channel_programs: dict[int, int] = {}

    abs_time = 0.0
    for msg in mid:
        abs_time += msg.time
        if msg.type == 'program_change':
            channel_programs[msg.channel] = msg.program
            continue
        if msg.type != 'note_on' or msg.velocity == 0:
            continue

        housing_tick = round(abs_time * 20)

        if msg.channel == 9:
            sound = MIDI_DRUM_TO_SOUND.get(msg.note, MIDI_DRUM_DEFAULT)
            pitch = 1.0
        else:
            program = channel_programs.get(msg.channel, 0)
            sound = _midi_program_to_sound(program)
            pitch = _midi_note_to_pitch(msg.note, clamp_pitch=clamp_pitch)

        volume = msg.velocity / 127
        events.append(
            NoteEvent(
                housing_tick=housing_tick,
                sound=sound,
                volume=volume,
                pitch=pitch,
            )
        )

    return events


def music_into_note_events(
    path: str | Path,
    *,
    clamp_pitch: bool = True,
    time_range: tuple[float, float] | None = None,
) -> list[NoteEvent]:
    path = Path(path)
    if path.suffix.lower() == '.nbs':
        events = _events_from_nbs(path, clamp_pitch=clamp_pitch)
    elif path.suffix.lower() == '.mid' or path.suffix.lower() == '.midi':
        events = _events_from_midi(path, clamp_pitch=clamp_pitch)
    else:
        raise ValueError(f'Unsupported music file format: {path.suffix}')

    if time_range is not None:
        start_tick = round(time_range[0] * 20)
        end_tick = round(time_range[1] * 20)
        events = [e for e in events if start_tick <= e.housing_tick <= end_tick]

    return events


def music_into_expressions(
    path: str | Path,
    *,
    clamp_pitch: bool = True,
    time_range: tuple[float, float] | None = None,
    strip_pauses: bool = True,
    sound_factory: Callable[[NoteEvent], PlaySoundExpression] | None = None,
    sound_transform: Callable[[PlaySoundExpression], PlaySoundExpression | None]
    | None = None,
    sound_filter: Callable[[PlaySoundExpression], bool] | None = None,
) -> list[Expression]:
    events = music_into_note_events(
        path,
        clamp_pitch=clamp_pitch,
        time_range=time_range,
    )
    return note_events_into_expressions(
        events,
        strip_pauses=strip_pauses,
        sound_factory=sound_factory,
        sound_transform=sound_transform,
        sound_filter=sound_filter,
    )
