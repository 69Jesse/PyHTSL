import atexit
import random
import threading
import wave
from pathlib import Path
from typing import get_args

import numpy as np
import sounddevice as sd

from ..types import ALL_SOUNDS, ALL_SOUNDS_PRETTY_TO_RAW, ALL_SOUNDS_RAW

__all__ = ('get_sound_paths', 'play')


_SAMPLE_RATE = 44100
_CHANNELS = 1


class Mixer:
    voices: list[tuple[np.ndarray, int]]  # (data, offset)
    stream: sd.OutputStream | None
    _lock: threading.Lock

    def __init__(self) -> None:
        self.voices = []
        self.stream = None
        self._lock = threading.Lock()

    def _ensure_stream(self) -> None:
        if self.stream is not None and self.stream.active:
            return
        if self.stream is not None:
            self.stream.close()
        self.stream = sd.OutputStream(
            samplerate=_SAMPLE_RATE,
            channels=_CHANNELS,
            dtype='float32',
            callback=self._callback,
        )
        self.stream.start()

    def _callback(
        self,
        outdata: np.ndarray,
        frames: int,
        _time: object,
        _status: object,
    ) -> None:
        outdata[:] = 0
        with self._lock:
            still_active: list[tuple[np.ndarray, int]] = []
            for data, offset in self.voices:
                remaining = len(data) - offset
                if remaining <= 0:
                    continue
                chunk = min(frames, remaining)
                outdata[:chunk] += data[offset : offset + chunk]
                if offset + chunk < len(data):
                    still_active.append((data, offset + chunk))
            self.voices = still_active
        if not still_active:
            raise sd.CallbackStop

    def add(self, data: np.ndarray, sample_rate: int) -> None:
        if sample_rate != _SAMPLE_RATE:
            ratio = _SAMPLE_RATE / sample_rate
            new_len = int(len(data) * ratio)
            old_indices = np.linspace(0, len(data) - 1, new_len)
            if data.ndim == 1:
                data = np.interp(old_indices, np.arange(len(data)), data).astype(
                    np.float32
                )
            else:
                resampled = np.empty((new_len, data.shape[1]), dtype=np.float32)
                for ch in range(data.shape[1]):
                    resampled[:, ch] = np.interp(
                        old_indices, np.arange(len(data)), data[:, ch]
                    )
                data = resampled

        if data.ndim > 1:
            data = data.mean(axis=1)
        data = data.reshape(-1, _CHANNELS)

        with self._lock:
            self.voices.append((data, 0))
        self._ensure_stream()

    def shutdown(self) -> None:
        if self.stream is not None:
            if self.stream.active:
                sd.sleep(
                    int(
                        max((len(d) - o) / _SAMPLE_RATE * 1000 for d, o in self.voices)
                        if self.voices
                        else 0
                    )
                )
            self.stream.close()
            self.stream = None
        self.voices.clear()


mixer = Mixer()
atexit.register(mixer.shutdown)


SOUNDS_DIR = Path(__file__).parent / 'sounds' / '1.8.9'

SOUND_OVERRIDES: dict[ALL_SOUNDS_RAW, str] = {
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
        if sound in SOUND_OVERRIDES:
            override = SOUND_OVERRIDES[sound]
            parent = SOUNDS_DIR / Path(override).parent
            stem = Path(override).name
            mapping[sound] = _find_files(parent, stem)
        else:
            mapping[sound] = _find_sound_files(sound.split('.'))
    return mapping


_MAPPING: dict[ALL_SOUNDS_RAW, list[Path]] | None = None


def _get_mapping() -> dict[ALL_SOUNDS_RAW, list[Path]]:
    global _MAPPING
    if _MAPPING is None:
        _MAPPING = _build_mapping()
    return _MAPPING


def get_sound_paths(raw_sound: ALL_SOUNDS_RAW) -> list[Path]:
    return _get_mapping().get(raw_sound, [])


_AUDIO_CACHE: dict[Path, tuple[np.ndarray, int]] = {}


def _load_wav(path: Path) -> tuple[np.ndarray, int]:
    cached = _AUDIO_CACHE.get(path)
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
    _AUDIO_CACHE[path] = result
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


def _housing_pitch(pitch: float) -> float:
    return 0.5 * (2**pitch)


def play(
    sound: ALL_SOUNDS,
    *,
    volume: float = 0.7,
    pitch: float = 1.0,
) -> bool:
    raw_sound: ALL_SOUNDS_RAW = ALL_SOUNDS_PRETTY_TO_RAW.get(sound, sound)  # type: ignore
    paths = get_sound_paths(raw_sound)
    if not paths:
        return False

    path = random.choice(paths)
    data, sample_rate = _load_wav(path)

    pitch = max(0.0, min(2.0, pitch))
    data = _resample(data, _housing_pitch(pitch))
    data = data * volume

    mixer.add(data, sample_rate)
    return True
