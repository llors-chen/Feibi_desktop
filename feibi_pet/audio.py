from __future__ import annotations

from pathlib import Path
import random
import threading
import time

import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
except Exception as exc:  # pragma: no cover - optional runtime dependency guard
    sd = None
    sf = None
    AUDIO_BACKEND_ERROR = exc
else:
    AUDIO_BACKEND_ERROR = None


class AudioPlayer:
    TAIL_SILENCE_SECONDS = 0.5

    def __init__(self) -> None:
        self.enabled = True
        self.volume = 1.0
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._stop_loop = threading.Event()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self.stop()

    def set_volume(self, volume_percent: int) -> None:
        clamped = max(0, min(150, int(volume_percent)))
        self.volume = clamped / 100.0

    def play_random(self, sound_paths: list[Path]) -> None:
        if not self.enabled or not sound_paths:
            return
        self.play_file(random.choice(sound_paths))

    def play_file(self, sound_path: Path) -> None:
        if not self.enabled:
            return
        if sd is None or sf is None:
            if AUDIO_BACKEND_ERROR is not None:
                print(f"Audio backend unavailable: {AUDIO_BACKEND_ERROR}")
            return

        with self._lock:
            self.stop()

            def worker() -> None:
                try:
                    data, sample_rate = sf.read(str(sound_path), dtype="float32")
                    if self.volume != 1.0:
                        data = data * self.volume
                    data = self._append_tail_silence(data, sample_rate)
                    sd.play(data, sample_rate)
                    sd.wait()
                except Exception as exc:
                    print(f"Audio playback failed for {sound_path}: {exc}")

            self._thread = threading.Thread(target=worker, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        if sd is not None:
            sd.stop()
        self._stop_loop.set()

    def play_loop(self, sound_paths: list[Path], pause_seconds: float = 2.0) -> None:
        if not self.enabled or not sound_paths:
            return

        with self._lock:
            self._stop_loop.set()
            self.stop()

            def worker() -> None:
                self._stop_loop.clear()
                while not self._stop_loop.is_set():
                    sound_path = random.choice(sound_paths)
                    try:
                        data, sample_rate = sf.read(str(sound_path), dtype="float32")
                        if self.volume != 1.0:
                            data = data * self.volume
                        data = self._append_tail_silence(data, sample_rate)
                        sd.play(data, sample_rate)
                        sd.wait()
                        if self._stop_loop.is_set():
                            break
                        pause_count = int(pause_seconds * 10)
                        for _ in range(pause_count):
                            if self._stop_loop.is_set():
                                break
                            time.sleep(0.1)
                    except Exception as exc:
                        print(f"Audio loop playback failed for {sound_path}: {exc}")
                        break

            self._thread = threading.Thread(target=worker, daemon=True)
            self._thread.start()

    def stop_loop(self) -> None:
        self._stop_loop.set()
        self.stop()

    def close(self) -> None:
        self.stop()

    def _append_tail_silence(self, data: np.ndarray, sample_rate: int) -> np.ndarray:
        padding_frames = int(sample_rate * self.TAIL_SILENCE_SECONDS)
        if padding_frames <= 0:
            return data
        if data.ndim == 1:
            padding_shape = (padding_frames,)
        else:
            padding_shape = (padding_frames, data.shape[1])
        padding = np.zeros(padding_shape, dtype=data.dtype)
        return np.concatenate((data, padding), axis=0)
