import difflib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast, get_args

import mido
import pynbs

from pyhtsw.actions.flow import PauseExecutionExpression
from pyhtsw.actions.world import PlaySoundExpression
from pyhtsw.expression.expression import Expression
from pyhtsw.generated.enums import SOUND_NAME_TO_PATH, Sound
from pyhtsw.utils.warn import warn

__all__ = (
    'NoteEvent',
    'CustomInstrumentResolver',
    'note_events_into_expressions',
    'nbs_into_note_events',
    'midi_into_note_events',
    'nbs_into_expressions',
    'midi_into_expressions',
)

CustomInstrumentResolver = Callable[[str], Sound | None]


# NBS instrument ID -> Housing sound (raw)
# 0-6 are 1.8.9 vanilla, 7-15 are 1.12+ (mapped to closest 1.8.9 equivalent)
NBS_INSTRUMENT_TO_SOUND: dict[int, Sound] = {
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
MIDI_PROGRAM_TO_SOUND: dict[range, Sound] = {
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
MIDI_DRUM_TO_SOUND: dict[int, Sound] = {
    35: 'note.bd',
    36: 'note.bd',  # Bass Drum
    38: 'note.snare',
    40: 'note.snare',  # Snare
    42: 'note.hat',
    44: 'note.hat',
    46: 'note.hat',  # Hi-Hat
}
MIDI_DRUM_DEFAULT = 'note.hat'


def _normalize_sound_name(name: str) -> str:
    chars: list[str] = []
    for ch in name.lower():
        if 'a' <= ch <= 'z':
            chars.append(ch)
        elif not ch.isalnum():
            chars.append('.')
        # digits dropped
    normalized = ''.join(chars)
    while '..' in normalized:
        normalized = normalized.replace('..', '.')
    return normalized.strip('.')


# Pretty names normalized like custom-instrument names, for direct lookup.
_NORMALIZED_PRETTY_TO_RAW: dict[str, Sound] = {
    _normalize_sound_name(pretty): raw for pretty, raw in SOUND_NAME_TO_PATH.items()
}
_ALL_RAW_SOUNDS: frozenset[str] = frozenset(get_args(Sound))


def _build_unique_tokens() -> dict[str, Sound]:
    token_raws: dict[str, set[Sound]] = {}
    for normalized_pretty, raw in _NORMALIZED_PRETTY_TO_RAW.items():
        for token in normalized_pretty.split('.'):
            if token:
                token_raws.setdefault(token, set()).add(raw)
    return {
        token: next(iter(raws)) for token, raws in token_raws.items() if len(raws) == 1
    }


_UNIQUE_TOKEN_TO_RAW: dict[str, Sound] = _build_unique_tokens()

_FUZZY_CUTOFF = 0.75


def _fuzzy_match(normalized: str) -> Sound | None:
    for token in normalized.split('.'):
        if not token:
            continue
        matches = difflib.get_close_matches(
            token,
            _UNIQUE_TOKEN_TO_RAW,
            n=1,
            cutoff=_FUZZY_CUTOFF,
        )
        if matches:
            return _UNIQUE_TOKEN_TO_RAW[matches[0]]
    return None


def _resolve_custom_instrument(
    name: str,
    resolver: CustomInstrumentResolver | None,
) -> Sound:
    normalized = _normalize_sound_name(name)
    if resolver is not None:
        override = resolver(normalized)
        if override is not None:
            return override
    candidate = _NORMALIZED_PRETTY_TO_RAW.get(normalized, normalized)
    if candidate in _ALL_RAW_SOUNDS:
        return cast(Sound, candidate)
    fuzzy = _fuzzy_match(normalized)
    if fuzzy is not None:
        warn(f'Using {fuzzy} for custom sound {name!r}')
        return fuzzy
    warn(f'Could not find sound {name!r}, falling back to note.harp')
    return 'note.harp'


def _midi_program_to_sound(program: int) -> Sound:
    for r, sound in MIDI_PROGRAM_TO_SOUND.items():
        if program in r:
            return sound
    return 'note.harp'


def _nbs_key_to_pitch(
    key: float,
    *,
    clamp_pitch: bool = True,
) -> float:
    pitch = 2 ** ((key - 45) / 12)
    if clamp_pitch:
        pitch = max(0.0, min(2.0, pitch))
    return pitch


def _midi_note_to_pitch(
    note: int,
    *,
    clamp_pitch: bool = True,
) -> float:
    return _nbs_key_to_pitch(note - 21, clamp_pitch=clamp_pitch)


@dataclass
class NoteEvent:
    housing_tick: int
    sound: Sound
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
    custom_instrument_resolver: CustomInstrumentResolver | None = None,
) -> list[NoteEvent]:
    song = pynbs.read(str(path))
    tps = song.header.tempo
    events: list[NoteEvent] = []

    layer_volumes: dict[int, float] = {}
    for i, layer in enumerate(song.layers):
        layer_volumes[i] = layer.volume / 100

    # Custom instruments follow the built-ins: note.instrument == 16 + custom id.
    builtin_count = len(NBS_INSTRUMENT_TO_SOUND)
    custom_names: dict[int, str] = {
        builtin_count + inst.id: inst.name or '' for inst in song.instruments
    }
    # Resolved lazily on first use, so unused instruments never log a note.
    custom_sounds: dict[int, Sound] = {}

    for tick, chord in song:
        housing_tick = round(tick * 20 / tps)
        for note in chord:
            sound = NBS_INSTRUMENT_TO_SOUND.get(note.instrument)
            if sound is None:
                if note.instrument not in custom_sounds:
                    name = custom_names.get(note.instrument, '')
                    custom_sounds[note.instrument] = _resolve_custom_instrument(
                        name,
                        custom_instrument_resolver,
                    )
                sound = custom_sounds[note.instrument]
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
                ),
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
            ),
        )

    return events


def _filter_time_range(
    events: list[NoteEvent],
    time_range: tuple[float, float] | None,
) -> list[NoteEvent]:
    if time_range is None:
        return events
    start_tick = round(time_range[0] * 20)
    end_tick = round(time_range[1] * 20)
    return [e for e in events if start_tick <= e.housing_tick <= end_tick]


def nbs_into_note_events(
    path: str | Path,
    *,
    clamp_pitch: bool = True,
    time_range: tuple[float, float] | None = None,
    custom_instrument_resolver: CustomInstrumentResolver | None = None,
) -> list[NoteEvent]:
    events = _events_from_nbs(
        Path(path),
        clamp_pitch=clamp_pitch,
        custom_instrument_resolver=custom_instrument_resolver,
    )
    return _filter_time_range(events, time_range)


def midi_into_note_events(
    path: str | Path,
    *,
    clamp_pitch: bool = True,
    time_range: tuple[float, float] | None = None,
) -> list[NoteEvent]:
    events = _events_from_midi(Path(path), clamp_pitch=clamp_pitch)
    return _filter_time_range(events, time_range)


def nbs_into_expressions(
    path: str | Path,
    *,
    clamp_pitch: bool = True,
    time_range: tuple[float, float] | None = None,
    custom_instrument_resolver: CustomInstrumentResolver | None = None,
    strip_pauses: bool = True,
    sound_factory: Callable[[NoteEvent], PlaySoundExpression] | None = None,
    sound_transform: Callable[[PlaySoundExpression], PlaySoundExpression | None]
    | None = None,
    sound_filter: Callable[[PlaySoundExpression], bool] | None = None,
) -> list[Expression]:
    events = nbs_into_note_events(
        path,
        clamp_pitch=clamp_pitch,
        time_range=time_range,
        custom_instrument_resolver=custom_instrument_resolver,
    )
    return note_events_into_expressions(
        events,
        strip_pauses=strip_pauses,
        sound_factory=sound_factory,
        sound_transform=sound_transform,
        sound_filter=sound_filter,
    )


def midi_into_expressions(
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
    events = midi_into_note_events(
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
