---
name: fourier
description: This skill should be used when the user asks to "run a Fourier transform", "analyze frequency content", "plot the spectrum", "find dominant frequencies", or "FFT" a signal. Works on CSV data, WAV audio files, or inline arrays.
argument-hint: "[file.csv | file.wav | --demo]"
---

# Fourier Analysis

Analyze the frequency content of a signal using FFT and produce a spectrum plot.

## Requirements

Install dependencies with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv pip install -r ${CLAUDE_SKILL_DIR}/requirements.txt
```

Or create an isolated virtual environment for the skill:

```bash
uv venv ${CLAUDE_SKILL_DIR}/.venv
uv pip install -r ${CLAUDE_SKILL_DIR}/requirements.txt --python ${CLAUDE_SKILL_DIR}/.venv/bin/python
```

Then run scripts with:

```bash
uv run --with numpy --with matplotlib --with scipy python ${CLAUDE_SKILL_DIR}/scripts/fft_plot.py --demo
```

Or with pip:

```bash
pip install -r ${CLAUDE_SKILL_DIR}/requirements.txt
```

## Usage

### Demo mode (no input needed)

Generates a synthetic signal (3 sine waves at 5 Hz, 50 Hz, 120 Hz + noise):

```bash
uv run --with numpy --with matplotlib --with scipy \
  python ${CLAUDE_SKILL_DIR}/scripts/fft_plot.py --demo
```

### From a CSV file

Two-column (time, amplitude) or single-column (amplitude only):

```bash
uv run --with numpy --with matplotlib --with scipy \
  python ${CLAUDE_SKILL_DIR}/scripts/fft_plot.py path/to/signal.csv
```

Override sample rate for single-column CSV (default: 1000 Hz):

```bash
uv run --with numpy --with matplotlib --with scipy \
  python ${CLAUDE_SKILL_DIR}/scripts/fft_plot.py signal.csv --sample-rate 44100
```

### From a WAV file

```bash
uv run --with numpy --with matplotlib --with scipy \
  python ${CLAUDE_SKILL_DIR}/scripts/fft_plot.py path/to/audio.wav
```

## Steps

1. Check what input the user provided — file path or `--demo`
2. If no dependencies installed, run `uv pip install -r ${CLAUDE_SKILL_DIR}/requirements.txt`
3. Run the script with the appropriate argument
4. The script saves `spectrum.png` in the current directory and prints dominant frequencies to stdout
5. Report the top frequencies and show the path to the plot

## Examples

Generate example CSV files to test with:

```bash
uv run --with numpy python ${CLAUDE_SKILL_DIR}/examples/generate.py
```

This creates:
- `two_tones.csv` — 10 Hz + 30 Hz sine waves, two-column format (time, amplitude)
- `sine_50hz.csv` — pure 50 Hz tone, single-column format

## Output

- `spectrum.png` — magnitude spectrum (frequency vs amplitude)
- Stdout: top 5 dominant frequencies with their amplitudes

## Notes

- Sample rate is read from WAV headers automatically
- Hann window applied before FFT to reduce spectral leakage
- Only positive frequencies plotted (DC to Nyquist)
