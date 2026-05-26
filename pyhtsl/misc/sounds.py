import random
import threading
import wave
from pathlib import Path
from typing import get_args

import numpy as np
import sounddevice as sd

from ..types import ALL_SOUNDS, ALL_SOUNDS_PRETTY_TO_RAW, ALL_SOUNDS_RAW

__all__ = ('get_sound_paths', 'preview_sound')


_SAMPLE_RATE = 44100
_CHANNELS = 1


class Mixer:
    voices: list[list]  # [data, offset]
    stream: sd.OutputStream | None
    played: bool
    _lock: threading.Lock

    def __init__(self) -> None:
        self.voices = []
        self.stream = None
        self.played = False
        self._lock = threading.Lock()

    def _callback(
        self,
        outdata: np.ndarray,
        frames: int,
        _time: object,
        _status: object,
    ) -> None:
        outdata.fill(0)
        with self._lock:
            still_active: list[list] = []
            for voice in self.voices:
                data, offset = voice
                remaining = len(data) - offset
                if remaining <= 0:
                    continue
                chunk = min(frames, remaining)
                outdata[:chunk, 0] += data[offset : offset + chunk]
                new_offset = offset + chunk
                if new_offset < len(data):
                    voice[1] = new_offset
                    still_active.append(voice)
            self.voices = still_active
        # Soft-limit so overlapping voices compress instead of clipping harshly.
        np.tanh(outdata, out=outdata)

    def add(self, data: np.ndarray) -> None:
        with self._lock:
            self.voices.append([data, 0])
            self.played = True
            if self.stream is None or not self.stream.active:
                if self.stream is not None:
                    self.stream.close()
                self.stream = sd.OutputStream(
                    samplerate=_SAMPLE_RATE,
                    channels=_CHANNELS,
                    dtype='float32',
                    callback=self._callback,
                )
                self.stream.start()

    def shutdown(self) -> None:
        with self._lock:
            stream = self.stream
            self.stream = None
            voices = self.voices
            self.voices = []
        try:
            still_active = stream is not None and stream.active
        except sd.PortAudioError:
            # PortAudio's own atexit ran first; nothing to wait on or close.
            return
        if still_active and voices:
            max_ms = int(max((len(d) - o) / _SAMPLE_RATE * 1000 for d, o in voices)) + 100
            sd.sleep(max_ms)
        if stream is not None:
            try:
                stream.close()
            except sd.PortAudioError:
                pass


SOUND_MIXER = Mixer()


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


_AUDIO_CACHE: dict[Path, np.ndarray] = {}


def _load_wav(path: Path) -> np.ndarray:
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
        data = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif sample_width == 2:
        data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 4:
        data = np.frombuffer(raw_data, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f'Unsupported sample width: {sample_width}')

    if n_channels > 1:
        data = data.reshape(-1, n_channels).mean(axis=1)

    if sample_rate != _SAMPLE_RATE:
        ratio = _SAMPLE_RATE / sample_rate
        new_len = int(len(data) * ratio)
        if new_len > 0:
            old_indices = np.linspace(0, len(data) - 1, new_len)
            data = np.interp(old_indices, np.arange(len(data)), data).astype(np.float32)

    data = np.ascontiguousarray(data, dtype=np.float32)
    _AUDIO_CACHE[path] = data
    return data


def _resample(data: np.ndarray, pitch: float) -> np.ndarray:
    if pitch == 1.0:
        return data
    if pitch <= 0.0:
        return data[:1]

    n_frames = len(data)
    new_length = int(n_frames / pitch)
    if new_length <= 0:
        return data[:1]

    old_indices = np.linspace(0, n_frames - 1, new_length)
    return np.interp(old_indices, np.arange(n_frames), data).astype(np.float32)


def preview_sound(
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
    data = _load_wav(path)
    data = _resample(data, pitch)
    if volume != 1.0:
        data = data * np.float32(volume)

    SOUND_MIXER.add(data)
    return True
