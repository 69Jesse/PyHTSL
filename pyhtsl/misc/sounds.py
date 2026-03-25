import random
import wave
from pathlib import Path
from typing import get_args

import numpy as np
import sounddevice as sd

from ..types import ALL_SOUNDS, ALL_SOUNDS_PRETTY_TO_RAW, ALL_SOUNDS_RAW

__all__ = ('get_sound_paths', 'play')


SOUNDS_DIR = Path(__file__).parent / 'sounds' / '1.8.9'

_SOUND_OVERRIDES: dict[str, str] = {
    'game.player.hurt.fall.big': 'damage/fallbig',
    'game.player.hurt.fall.small': 'damage/fallsmall',
    'game.tnt.primed': 'random/fuse',
    'dig.glass': 'random/glass',
    'game.player.hurt': 'damage/hit',
    'game.player.swim.splash': 'liquid/splash',
    'game.player.swim': 'liquid/swim',
    'mob.guardian.attack': 'mob/guardian/attack_loop',
    'mob.rabbit.death': 'mob/rabbit/bunnymurder',
}


def _find_files(directory: Path, stem: str) -> list[Path]:
    exact = directory / f'{stem}.wav'
    numbered = sorted(directory.glob(f'{stem}[0-9]*.wav'))
    results: list[Path] = []
    if exact.is_file():
        results.append(exact)
    results.extend(numbered)
    return results


def _find_sound_files(parts: list[str]) -> list[Path]:
    for split_point in range(len(parts) - 1, 0, -1):
        directory = SOUNDS_DIR / Path(*parts[:split_point])
        if not directory.is_dir():
            continue

        stem = '_'.join(parts[split_point:])
        files = _find_files(directory, stem)
        if files:
            return files

        prefixed_stem = parts[split_point - 1] + '_' + stem
        files = _find_files(directory, prefixed_stem)
        if files:
            return files

    return []


def _build_mapping() -> dict[ALL_SOUNDS_RAW, list[Path]]:
    mapping: dict[ALL_SOUNDS_RAW, list[Path]] = {}
    for sound in get_args(ALL_SOUNDS_RAW):
        if sound in _SOUND_OVERRIDES:
            override = _SOUND_OVERRIDES[sound]
            parent = SOUNDS_DIR / Path(override).parent
            stem = Path(override).name
            mapping[sound] = _find_files(parent, stem)
        else:
            mapping[sound] = _find_sound_files(sound.split('.'))
    return mapping


_mapping: dict[ALL_SOUNDS_RAW, list[Path]] | None = None


def _get_mapping() -> dict[ALL_SOUNDS_RAW, list[Path]]:
    global _mapping
    if _mapping is None:
        _mapping = _build_mapping()
    return _mapping


def get_sound_paths(raw_sound: ALL_SOUNDS_RAW) -> list[Path]:
    return _get_mapping().get(raw_sound, [])


_audio_cache: dict[Path, tuple[np.ndarray, int]] = {}


def _load_wav(path: Path) -> tuple[np.ndarray, int]:
    cached = _audio_cache.get(path)
    if cached is not None:
        return cached

    with wave.open(str(path), 'rb') as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw_data = wf.readframes(n_frames)

    if sample_width == 1:
        dtype = np.uint8
    elif sample_width == 2:
        dtype = np.int16
    elif sample_width == 4:
        dtype = np.int32
    else:
        raise ValueError(f'Unsupported sample width: {sample_width}')

    data = np.frombuffer(raw_data, dtype=dtype).astype(np.float32)

    if dtype == np.uint8:
        data = (data - 128) / 128
    elif dtype == np.int16:
        data /= 32768
    elif dtype == np.int32:
        data /= 2147483648

    if n_channels > 1:
        data = data.reshape(-1, n_channels)

    result = (data, sample_rate)
    _audio_cache[path] = result
    return result


def _resample(data: np.ndarray, pitch: float) -> np.ndarray:
    if pitch == 1.0:
        return data

    n_frames = len(data)
    new_length = int(n_frames / pitch)
    if new_length == 0:
        return data[:1]

    old_indices = np.linspace(0, n_frames - 1, new_length)

    if data.ndim == 1:
        return np.interp(old_indices, np.arange(n_frames), data).astype(np.float32)

    result = np.empty((new_length, data.shape[1]), dtype=np.float32)
    for ch in range(data.shape[1]):
        result[:, ch] = np.interp(old_indices, np.arange(n_frames), data[:, ch])
    return result


def play(sound: ALL_SOUNDS, volume: float, pitch: float) -> bool:
    raw_sound: ALL_SOUNDS_RAW = ALL_SOUNDS_PRETTY_TO_RAW.get(sound, sound)  # type: ignore
    paths = get_sound_paths(raw_sound)
    if not paths:
        return False

    path = random.choice(paths)
    data, sample_rate = _load_wav(path)

    pitch = max(0.0, min(2.0, pitch))
    if pitch == 0.0:
        return True

    data = _resample(data, pitch)
    data = data * volume

    print(list(data))
    sd.play(data, samplerate=sample_rate)
    return True
