#!/usr/bin/env python3
"""FFT spectrum analyzer — reads CSV or WAV, plots magnitude spectrum."""

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def load_csv(path: Path, sample_rate: float) -> tuple[np.ndarray, float]:
    data = np.loadtxt(path, delimiter=",")
    if data.ndim == 2 and data.shape[1] == 2:
        # Two-column: time, amplitude — infer sample rate from time column
        dt = np.median(np.diff(data[:, 0]))
        sample_rate = 1.0 / dt
        signal = data[:, 1]
    else:
        signal = data.flatten()
    return signal, sample_rate


def load_wav(path: Path) -> tuple[np.ndarray, float]:
    from scipy.io import wavfile
    rate, data = wavfile.read(path)
    if data.ndim == 2:
        data = data.mean(axis=1)  # stereo -> mono
    signal = data.astype(np.float64)
    signal /= np.max(np.abs(signal)) or 1.0  # normalize
    return signal, float(rate)


def make_demo_signal(sample_rate: float = 1000.0, duration: float = 1.0) -> np.ndarray:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal = (
        1.0 * np.sin(2 * np.pi * 5 * t)
        + 0.6 * np.sin(2 * np.pi * 50 * t)
        + 0.3 * np.sin(2 * np.pi * 120 * t)
        + 0.1 * np.random.randn(len(t))
    )
    return signal


def compute_spectrum(signal: np.ndarray, sample_rate: float) -> tuple[np.ndarray, np.ndarray]:
    windowed = signal * np.hanning(len(signal))
    fft_vals = np.fft.rfft(windowed)
    freqs = np.fft.rfftfreq(len(signal), d=1.0 / sample_rate)
    magnitude = np.abs(fft_vals) / len(signal)
    return freqs, magnitude


def top_frequencies(freqs: np.ndarray, magnitude: np.ndarray, n: int = 5) -> list[tuple[float, float]]:
    # Exclude DC (index 0)
    indices = np.argsort(magnitude[1:])[::-1][:n] + 1
    return [(freqs[i], magnitude[i]) for i in indices]


def plot_spectrum(freqs: np.ndarray, magnitude: np.ndarray, title: str, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(freqs, magnitude, linewidth=0.8, color="#2563eb")
    ax.fill_between(freqs, magnitude, alpha=0.15, color="#2563eb")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude")
    ax.set_title(title)
    ax.set_xlim(0, freqs[-1])
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="FFT spectrum analyzer")
    parser.add_argument("input", nargs="?", help="CSV or WAV file")
    parser.add_argument("--demo", action="store_true", help="Run with synthetic demo signal")
    parser.add_argument("--sample-rate", type=float, default=1000.0, metavar="HZ",
                        help="Sample rate for CSV input (default: 1000 Hz)")
    parser.add_argument("--out", default="spectrum.png", help="Output image path")
    args = parser.parse_args()

    if args.demo:
        signal = make_demo_signal(args.sample_rate)
        sample_rate = args.sample_rate
        title = "Demo signal: 5 Hz + 50 Hz + 120 Hz + noise"
    elif args.input:
        path = Path(args.input)
        if not path.exists():
            sys.exit(f"Error: file not found: {path}")
        if path.suffix.lower() == ".wav":
            signal, sample_rate = load_wav(path)
            title = f"Spectrum — {path.name}"
        else:
            signal, sample_rate = load_csv(path, args.sample_rate)
            title = f"Spectrum — {path.name}"
    else:
        parser.print_help()
        sys.exit(1)

    freqs, magnitude = compute_spectrum(signal, sample_rate)

    out_path = Path(args.out)
    plot_spectrum(freqs, magnitude, title, out_path)

    print(f"Saved: {out_path.resolve()}")
    print(f"\nTop frequencies (sample rate: {sample_rate:.0f} Hz):")
    for freq, amp in top_frequencies(freqs, magnitude):
        print(f"  {freq:8.2f} Hz   amplitude: {amp:.4f}")


if __name__ == "__main__":
    main()
