#!/usr/bin/env python3
"""Generate example CSV signals for testing the fourier skill."""

import numpy as np
from pathlib import Path

out = Path(__file__).parent

# 10 Hz + 30 Hz sine waves, 1 second at 200 Hz sample rate
sample_rate = 200
t = np.linspace(0, 1, sample_rate, endpoint=False)
signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 30 * t)

rows = np.column_stack([t, signal])
np.savetxt(out / "two_tones.csv", rows, delimiter=",", fmt="%.6f")
print(f"Wrote {out / 'two_tones.csv'} — 10 Hz + 30 Hz, {sample_rate} Hz sample rate")

# Single amplitude column (no time), 50 Hz tone at 1000 Hz sample rate
sample_rate2 = 1000
t2 = np.linspace(0, 1, sample_rate2, endpoint=False)
signal2 = np.sin(2 * np.pi * 50 * t2)
np.savetxt(out / "sine_50hz.csv", signal2, fmt="%.6f")
print(f"Wrote {out / 'sine_50hz.csv'} — 50 Hz pure tone, {sample_rate2} Hz sample rate")
