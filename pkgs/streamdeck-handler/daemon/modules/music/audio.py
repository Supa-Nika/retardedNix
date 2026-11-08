"""System-audio spectrum analyser (PulseAudio/PipeWire monitor via parec -> FFT)."""
import subprocess
import threading
import time

import numpy as np

RATE = 44100
N = 2048        # FFT window
HOP = 1024      # new samples per update (~43 updates/s)
BANDS = 32


class AudioAnalyzer:
    def __init__(self, bands=BANDS):
        self.bands = bands
        self.levels = np.zeros(bands, dtype=np.float32)
        self.pulse = 0.0    # bass-driven beat envelope 0..1
        self.energy = 0.0   # overall loudness 0..1

        self._lock = threading.Lock()
        self._refs = 0
        self._thread = None
        self._stop = threading.Event()
        self._proc = None

        freqs = np.fft.rfftfreq(N, 1.0 / RATE)
        edges = np.geomspace(40, 14000, bands + 1)
        self._idx = []
        for i in range(bands):
            a = int(np.searchsorted(freqs, edges[i]))
            b = max(int(np.searchsorted(freqs, edges[i + 1])), a + 1)
            self._idx.append((a, b))
        self._win = np.hanning(N).astype(np.float32)
        self._tilt = np.geomspace(1.0, 5.0, bands).astype(np.float32)  # highs carry less energy
        self._peak = 0.01
        self._bass_avg = 0.0

    def acquire(self):
        with self._lock:
            self._refs += 1
            if self._thread is None:
                self._stop.clear()
                self._thread = threading.Thread(target=self._run, daemon=True)
                self._thread.start()

    def release(self):
        with self._lock:
            self._refs = max(0, self._refs - 1)
            if self._refs == 0 and self._thread is not None:
                self._stop.set()
                self._thread = None
                if self._proc is not None:
                    try:
                        self._proc.terminate()
                    except Exception:
                        pass

    def _run(self):
        warned = False
        while not self._stop.is_set():
            try:
                self._proc = subprocess.Popen(
                    ["parec", "--format=s16le", f"--rate={RATE}", "--channels=1", "--raw",
                     "--latency-msec=20", "-d", "@DEFAULT_MONITOR@"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                if not warned:
                    print("[Audio] 'parec' not found - visualiser disabled")
                    warned = True
                self._stop.wait(5)
                continue

            buf = np.zeros(N, dtype=np.float32)
            try:
                while not self._stop.is_set():
                    data = self._proc.stdout.read(HOP * 2)
                    if len(data) < HOP * 2:
                        break
                    chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    buf = np.concatenate((buf[HOP:], chunk))
                    self._analyse(buf)
            finally:
                try:
                    self._proc.terminate()
                except Exception:
                    pass
            self._stop.wait(2)

    def _analyse(self, buf):
        spec = np.abs(np.fft.rfft(buf * self._win)) / (N / 2)
        vals = np.array([spec[a:b].max() for a, b in self._idx], dtype=np.float32) * self._tilt

        self._peak = max(float(vals.max()), self._peak * 0.998, 0.004)
        db = 20.0 * np.log10(vals / self._peak + 1e-6)
        target = np.clip((db + 45.0) / 45.0, 0.0, 1.0)

        old = self.levels
        self.levels = np.where(target > old, old + (target - old) * 0.7, old * 0.85 + target * 0.15).astype(np.float32)

        bass = float(self.levels[:4].mean())
        self._bass_avg += (bass - self._bass_avg) * 0.05
        p = float(np.clip((bass - self._bass_avg) * 4.0, 0.0, 1.0))
        self.pulse = p if p > self.pulse else self.pulse * 0.85
        self.energy = float(self.levels.mean())


analyzer = AudioAnalyzer()
